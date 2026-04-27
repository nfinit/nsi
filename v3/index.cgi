#!/usr/bin/perl
# NSI: The New Standard Index ----------------------------------------------- #
my $version = '3.0.0.14';
# --------------------------------------------------------------------------- #

use strict;
use warnings;

use Cwd qw(cwd abs_path);
use File::Basename qw(basename dirname);
use Getopt::Long qw(GetOptions);
use Time::HiRes qw(time);

my $SITE_CONFIG_NAME  = "res/config.conf";
my $LOCAL_CONFIG_NAME = ".config.conf";

my %RUNTIME = (
  mode          => undef,
  cli_root      => undef,
  cli_target    => undef,
  cli_config    => undef,
  cli_verbose   => 0,
  help          => 0,
  document_root => undef,
  physical_cwd  => undef,
  logical_cwd   => undef,
  site_root     => undef,
  site_config   => undef,
  local_config  => undef,
  debug_html    => "",
);

my %CONFIG = (
  TITLE_FILE           => "title",
  INTRO_FILE           => "intro.html",
  BODY_FILE            => "body.html",
  TOC_FILE             => "info",
  GROUP_FILE           => "group",
  SITE_NAME            => "",
  ORGANIZATION         => "",
  NAV_POSITION         => "top",
  BREADCRUMB_SEPARATOR => " &gt; ",
  SHOW_TOC             => 1,
  TREE_TOC             => 1,
  TOC_TITLE            => "",
  TOC_SUBTITLE         => "",
  APPEND_TOC_TO_BODY   => 1,
  HOME_PAGE_TITLE      => "Home",
  FOOTER_NAV           => 1,
  API_ENABLED          => 1,
  DEBUG_TRACE          => 0,
  FAVICON              => "/res/sys/favicon.ico",
  SITE_STYLE_DIRECTORY => "/res/style",
  MAIN_STYLESHEET      => undef,
  LEGACY_STYLESHEET    => undef,
  HTML_DOCTYPE         => 'HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"',
  PAGE_TITLE           => "",
  PAGE_SUBTITLE        => "",
  PAGE_INTRO           => "",
  PAGE_META_DESCRIPTION => "",
  PAGE_META_KEYWORDS    => "",
);

$CONFIG{MAIN_STYLESHEET}   = "$CONFIG{SITE_STYLE_DIRECTORY}/style.css";
$CONFIG{LEGACY_STYLESHEET} = "$CONFIG{SITE_STYLE_DIRECTORY}/legacy.css";

my $MAIN_STYLESHEET_EXPLICIT   = 0;
my $LEGACY_STYLESHEET_EXPLICIT = 0;

# --------------------------------------------------------------------------- #
# /// Core utility subroutines ///
# Shared helpers that multiple pipeline phases depend on
# --------------------------------------------------------------------------- #

sub detect_runtime_mode {
  return "cgi" if ($ENV{GATEWAY_INTERFACE} || $ENV{REQUEST_METHOD});
  return "cli";
}

sub usage_text {
  return <<"USAGE";
Usage: perl v3/index.cgi [options]

Options:
  --help         Show this help message
  --verbose      Enable debug tracing
  --root=PATH    Set DOCUMENT_ROOT
  --target=PATH  Validate and store a target directory for later feature use
  --config=FILE  Use an explicit site config file
USAGE
}

sub config_enabled {
  my ($value) = @_;
  return 0 unless defined($value);
  return 0 if ($value =~ /^(?:0|false|no|off)$/i);
  return 1 if ($value =~ /^(?:1|true|yes|on)$/i);
  return $value ? 1 : 0;
}

sub content_header {
  my ($type) = @_;
  $type = "text/html" unless defined($type) && $type ne "";
  return "Content-type: ${type}\n\n";
}

sub debug_enabled {
  return 1 if ($RUNTIME{cli_verbose});
  return config_enabled($CONFIG{DEBUG_TRACE});
}

sub debug_line {
  my ($phase, $message) = @_;
  return unless (debug_enabled());
  return unless (defined($message) && $message ne "");
  $phase = "general" unless defined($phase) && $phase ne "";
  my $line = "[" . sprintf("%.6f", time()) . "] [$phase] $message\n";

  if ($RUNTIME{mode} eq "cli") {
    print STDERR $line;
  } else {
    $line =~ s/--/- -/g;
    $RUNTIME{debug_html} .= $line;
  }
}

sub debug_comment_block {
  return "" unless ($RUNTIME{mode} eq "cgi");
  return "" unless ($RUNTIME{debug_html});
  return "<!--\n$RUNTIME{debug_html}-->\n";
}

sub html_escape {
  my ($text) = @_;
  $text = "" unless defined($text);
  $text =~ s/&/&amp;/g;
  $text =~ s/</&lt;/g;
  $text =~ s/>/&gt;/g;
  $text =~ s/"/&quot;/g;
  return $text;
}

sub emit_error {
  my ($message) = @_;
  $message = "Unknown error" unless defined($message) && $message ne "";

  if ($RUNTIME{mode} eq "cgi") {
    my $safe = html_escape($message);
    print content_header("text/html");
    print "<!DOCTYPE $CONFIG{HTML_DOCTYPE}>\n";
    print "<HTML>\n<HEAD>\n<TITLE>NSI Error</TITLE>\n</HEAD>\n<BODY>\n";
    print "<H1>NSI Error</H1>\n";
    print "<PRE>${safe}</PRE>\n";
    print "</BODY>\n</HTML>\n";
  } else {
    print STDERR "NSI error: ${message}\n";
  }
  exit 1;
}

sub normalize_path {
  my ($path) = @_;
  return unless defined($path) && $path ne "";
  $path =~ s{//+}{/}g;
  $path =~ s{/$}{} unless ($path eq "/");
  return $path || "/";
}

sub path_is_within {
  my ($path, $base) = @_;
  return 0 unless ($path && $base);
  $path = normalize_path($path);
  $base = normalize_path($base);
  return 1 if ($path eq $base);
  return ($path =~ /^\Q$base\E\//) ? 1 : 0;
}

sub read_text_file {
  my ($path) = @_;
  return unless ($path && -e $path);
  emit_error("File exists but is not readable: $path") unless (-r $path);
  open(my $fh, '<', $path) or emit_error("Failed to read file $path: $!");
  local $/;
  my $content = <$fh>;
  close($fh);
  return $content;
}

sub read_text_file_line {
  my ($path, $line_number) = @_;
  return unless ($path && -e $path);
  emit_error("File exists but is not readable: $path") unless (-r $path);
  open(my $fh, '<', $path) or emit_error("Failed to read file $path: $!");
  my $current = 0;
  my $line;
  while (my $candidate = <$fh>) {
    $current++;
    if ($current == $line_number) {
      $line = $candidate;
      last;
    }
  }
  close($fh);
  chomp($line) if defined($line);
  return $line;
}

# --------------------------------------------------------------------------- #
# /// Runtime and configuration loading ///
# Detect execution mode, resolve the current logical location, discover
# configuration, and finalize the runtime contract before page assembly
# --------------------------------------------------------------------------- #

sub parse_cli_options {
  local @ARGV = @ARGV;
  Getopt::Long::Configure("no_auto_abbrev", "no_ignore_case");
  my $ok = GetOptions(
    "help"     => \$RUNTIME{help},
    "verbose"  => \$RUNTIME{cli_verbose},
    "root=s"   => \$RUNTIME{cli_root},
    "target=s" => \$RUNTIME{cli_target},
    "config=s" => \$RUNTIME{cli_config},
  );
  emit_error("Error in command line arguments. Use --help for usage.")
    unless ($ok);
}

sub validate_cli_paths {
  if (defined($RUNTIME{cli_root})) {
    emit_error("--root path does not exist: $RUNTIME{cli_root}")
      unless (-e $RUNTIME{cli_root});
    emit_error("--root path is not a directory: $RUNTIME{cli_root}")
      unless (-d $RUNTIME{cli_root});
    my $root = abs_path($RUNTIME{cli_root});
    emit_error("Unable to resolve --root path: $RUNTIME{cli_root}") unless ($root);
    $RUNTIME{cli_root} = normalize_path($root);
  }

  if (defined($RUNTIME{cli_target})) {
    emit_error("--target path does not exist: $RUNTIME{cli_target}")
      unless (-e $RUNTIME{cli_target});
    emit_error("--target path is not a directory: $RUNTIME{cli_target}")
      unless (-d $RUNTIME{cli_target});
    my $target = abs_path($RUNTIME{cli_target});
    emit_error("Unable to resolve --target path: $RUNTIME{cli_target}") unless ($target);
    $RUNTIME{cli_target} = normalize_path($target);
  }

  if (defined($RUNTIME{cli_config})) {
    emit_error("--config file does not exist: $RUNTIME{cli_config}")
      unless (-e $RUNTIME{cli_config});
    emit_error("--config path is not a file: $RUNTIME{cli_config}")
      unless (-f $RUNTIME{cli_config});
    emit_error("--config file is not readable: $RUNTIME{cli_config}")
      unless (-r $RUNTIME{cli_config});
    my $config = abs_path($RUNTIME{cli_config});
    emit_error("Unable to resolve --config path: $RUNTIME{cli_config}") unless ($config);
    $RUNTIME{cli_config} = normalize_path($config);
  }
}

sub get_cgi_logical_dir {
  emit_error("CGI mode requires DOCUMENT_ROOT to be set")
    unless ($ENV{DOCUMENT_ROOT});
  emit_error("CGI mode requires SCRIPT_NAME to be set")
    unless ($ENV{SCRIPT_NAME});

  my $doc_root = normalize_path(abs_path($ENV{DOCUMENT_ROOT}) || $ENV{DOCUMENT_ROOT});
  my $script_name = $ENV{SCRIPT_NAME};
  my $script_dir = $script_name;
  $script_dir =~ s{/[^/]*$}{};
  $script_dir = "/" if ($script_dir eq "");

  return (
    normalize_path($doc_root . $script_dir),
    $doc_root,
  );
}

sub discover_site_config {
  my ($start_dir, $stop_dir) = @_;
  my $dir = normalize_path($start_dir);
  $stop_dir = normalize_path($stop_dir) if ($stop_dir);

  while ($dir) {
    my $candidate = "${dir}/${SITE_CONFIG_NAME}";
    debug_line("config discovery", "Checking $candidate");
    return ($candidate, $dir) if (-f $candidate);

    last if ($dir eq "/");
    last if ($stop_dir && $dir eq $stop_dir);
    $dir = normalize_path(dirname($dir));
  }

  return;
}

sub config_root_from_file {
  my ($path) = @_;
  return unless ($path);
  my $dir = normalize_path(dirname($path));
  return normalize_path(dirname($dir)) if (basename($dir) eq "res");
  return $dir;
}

sub load_config_file {
  my ($path, $scope) = @_;
  return unless ($path);
  emit_error("Configuration file is not readable: $path") unless (-r $path);

  debug_line("config discovery/load", "Loading ${scope} config $path");

  open(my $fh, '<', $path) or emit_error("Failed to open config $path: $!");
  my $line_number = 0;
  while (my $line = <$fh>) {
    $line_number++;
    chomp($line);
    next if ($line =~ /^\s*$/);
    next if ($line =~ /^\s*#/);

    unless ($line =~ /^\s*([A-Za-z_]\w*)\s*=\s*(.*?)\s*$/) {
      close($fh);
      emit_error("Malformed config line in $path at line $line_number: $line");
    }

    my ($key, $value) = ($1, $2);
    $value =~ s/^\s+//;
    $value =~ s/\s+$//;
    $value =~ s/^"(.*)"$/$1/;
    $value =~ s/^'(.*)'$/$1/;

    if ($key eq "site_name") {
      $CONFIG{SITE_NAME} = $value;
    } elsif ($key eq "organization") {
      $CONFIG{ORGANIZATION} = $value;
    } elsif ($key eq "nav_position") {
      $CONFIG{NAV_POSITION} = $value;
    } elsif ($key eq "breadcrumb_separator") {
      $CONFIG{BREADCRUMB_SEPARATOR} = $value;
    } elsif ($key eq "show_toc") {
      $CONFIG{SHOW_TOC} = $value;
    } elsif ($key eq "tree_toc") {
      $CONFIG{TREE_TOC} = $value;
    } elsif ($key eq "toc_title") {
      $CONFIG{TOC_TITLE} = $value;
    } elsif ($key eq "toc_subtitle") {
      $CONFIG{TOC_SUBTITLE} = $value;
    } elsif ($key eq "append_toc_to_body") {
      $CONFIG{APPEND_TOC_TO_BODY} = $value;
    } elsif ($key eq "home_page_title") {
      $CONFIG{HOME_PAGE_TITLE} = $value;
    } elsif ($key eq "footer_nav") {
      $CONFIG{FOOTER_NAV} = $value;
    } elsif ($key eq "api_enabled") {
      $CONFIG{API_ENABLED} = $value;
    } elsif ($key eq "debug_trace") {
      $CONFIG{DEBUG_TRACE} = $value;
    } elsif ($key eq "favicon") {
      $CONFIG{FAVICON} = $value;
    } elsif ($key eq "site_style_directory") {
      $CONFIG{SITE_STYLE_DIRECTORY} = $value;
      $CONFIG{MAIN_STYLESHEET}   = "$value/style.css"
        unless ($MAIN_STYLESHEET_EXPLICIT);
      $CONFIG{LEGACY_STYLESHEET} = "$value/legacy.css"
        unless ($LEGACY_STYLESHEET_EXPLICIT);
    } elsif ($key eq "main_stylesheet") {
      $CONFIG{MAIN_STYLESHEET} = $value;
      $MAIN_STYLESHEET_EXPLICIT = 1;
    } elsif ($key eq "legacy_stylesheet") {
      $CONFIG{LEGACY_STYLESHEET} = $value;
      $LEGACY_STYLESHEET_EXPLICIT = 1;
    } elsif ($key eq "page_title") {
      $CONFIG{PAGE_TITLE} = $value;
    } elsif ($key eq "page_subtitle") {
      $CONFIG{PAGE_SUBTITLE} = $value;
    } elsif ($key eq "page_intro") {
      $CONFIG{PAGE_INTRO} = $value;
    } elsif ($key eq "page_meta_description") {
      $CONFIG{PAGE_META_DESCRIPTION} = $value;
    } elsif ($key eq "page_meta_keywords") {
      $CONFIG{PAGE_META_KEYWORDS} = $value;
    }
  }
  close($fh);
}

sub resolve_runtime {
  $RUNTIME{mode} = detect_runtime_mode();
  parse_cli_options() if ($RUNTIME{mode} eq "cli");

  if ($RUNTIME{help}) {
    print usage_text();
    exit 0;
  }

  validate_cli_paths() if ($RUNTIME{mode} eq "cli");

  $RUNTIME{physical_cwd} = normalize_path(cwd());
  emit_error("Unable to determine current working directory")
    unless ($RUNTIME{physical_cwd} && -d $RUNTIME{physical_cwd});

  debug_line("runtime detection", "Mode: $RUNTIME{mode}");
  debug_line("runtime detection", "Physical cwd: $RUNTIME{physical_cwd}");

  if ($RUNTIME{mode} eq "cgi") {
    my ($logical_cwd, $document_root) = get_cgi_logical_dir();
    $RUNTIME{logical_cwd}   = $logical_cwd;
    $RUNTIME{document_root} = $document_root;
  } else {
    $RUNTIME{logical_cwd}   = $RUNTIME{physical_cwd};
    $RUNTIME{document_root} = $RUNTIME{cli_root} if ($RUNTIME{cli_root});
  }

  my $initial_document_root = defined($RUNTIME{document_root})
    ? $RUNTIME{document_root}
    : "(unset)";
  debug_line("path resolution", "Logical cwd: $RUNTIME{logical_cwd}");
  debug_line("path resolution", "Initial document root: $initial_document_root");

  if ($RUNTIME{cli_config}) {
    $RUNTIME{site_config} = $RUNTIME{cli_config};
    $RUNTIME{site_root}   = config_root_from_file($RUNTIME{cli_config});
  } else {
    my ($site_config, $site_root) = discover_site_config(
      $RUNTIME{logical_cwd},
      $RUNTIME{document_root},
    );
    $RUNTIME{site_config} = $site_config;
    $RUNTIME{site_root}   = $site_root;
  }

  emit_error("Site configuration file ($SITE_CONFIG_NAME) not found in any parent directory.")
    unless ($RUNTIME{site_config});

  if (!defined($RUNTIME{document_root}) || $RUNTIME{document_root} eq "") {
    $RUNTIME{document_root} = $RUNTIME{site_root};
  }
  $ENV{DOCUMENT_ROOT} = $RUNTIME{document_root} if ($RUNTIME{document_root});

  emit_error("Unable to resolve DOCUMENT_ROOT in CLI mode")
    if ($RUNTIME{mode} eq "cli" && !$RUNTIME{document_root});

  emit_error("Current directory is outside DOCUMENT_ROOT: $RUNTIME{logical_cwd} (DOCUMENT_ROOT: $RUNTIME{document_root})")
    unless (path_is_within($RUNTIME{logical_cwd}, $RUNTIME{document_root}));

  emit_error("Logical current directory is not a directory: $RUNTIME{logical_cwd}")
    unless (-d $RUNTIME{logical_cwd});

  debug_line("config discovery/load", "Resolved site config: $RUNTIME{site_config}");
  debug_line("path resolution", "Resolved document root: $RUNTIME{document_root}");

  load_config_file($RUNTIME{site_config}, "site");

  $RUNTIME{local_config} = normalize_path("$RUNTIME{logical_cwd}/${LOCAL_CONFIG_NAME}");
  if (-e $RUNTIME{local_config}) {
    emit_error("Local config path is not a file: $RUNTIME{local_config}")
      unless (-f $RUNTIME{local_config});
    load_config_file($RUNTIME{local_config}, "local override");
  } else {
    $RUNTIME{local_config} = undef;
  }

  if ($RUNTIME{cli_verbose}) {
    $CONFIG{DEBUG_TRACE} = 1;
  }

  my $local_override = defined($RUNTIME{local_config})
    ? $RUNTIME{local_config}
    : "(none)";
  my $target = defined($RUNTIME{cli_target})
    ? $RUNTIME{cli_target}
    : "(unset)";
  debug_line("config discovery/load", "Local override: $local_override");
  debug_line("runtime detection", "Target: $target");
}

# --------------------------------------------------------------------------- #
# /// Path and content resolution helpers ///
# These helpers translate between the logical current directory, filesystem
# content files, and site-relative URLs used during assembly
# --------------------------------------------------------------------------- #

sub content_file_path {
  my ($dir, $name) = @_;
  return normalize_path("${dir}/${name}");
}

sub read_content_file {
  my ($dir, $name) = @_;
  return read_text_file(content_file_path($dir, $name));
}

sub read_content_file_line {
  my ($dir, $name, $line) = @_;
  return read_text_file_line(content_file_path($dir, $name), $line);
}

sub current_directory_url {
  my $path = normalize_path($RUNTIME{logical_cwd});
  my $root = normalize_path($RUNTIME{document_root});
  return "/" if ($path eq $root);
  my $url = $path;
  $url =~ s/^\Q$root\E//;
  $url = "/" if (!$url);
  return $url;
}

sub url_for_dir {
  my ($dir) = @_;
  $dir = normalize_path($dir);
  my $root = normalize_path($RUNTIME{document_root});
  return "/" if ($dir eq $root);
  my $url = $dir;
  $url =~ s/^\Q$root\E//;
  $url = "/" if (!$url);
  return $url;
}

sub title_for_dir {
  my ($dir, $fallback) = @_;
  return $fallback unless ($dir && -d $dir);
  return read_content_file_line($dir, $CONFIG{TITLE_FILE}, 1)
    || read_content_file_line($dir, $CONFIG{TOC_FILE}, 1)
    || basename($dir)
    || $fallback;
}

sub page_is_root {
  return normalize_path($RUNTIME{logical_cwd}) eq normalize_path($RUNTIME{document_root});
}

sub get_navigation {
  return if (page_is_root());

  my @breadcrumbs = ({
    label   => $CONFIG{HOME_PAGE_TITLE},
    href    => "/",
    current => 0,
  });

  my $root = normalize_path($RUNTIME{document_root});
  my $current = normalize_path($RUNTIME{logical_cwd});
  my $relative = $current;
  $relative =~ s/^\Q$root\E\/?//;
  my @segments = grep { $_ ne "" } split(/\//, $relative);

  my $cursor = $root;
  for (my $i = 0; $i < @segments; $i++) {
    $cursor = normalize_path("${cursor}/$segments[$i]");
    push @breadcrumbs, {
      label   => title_for_dir($cursor, $segments[$i]),
      href    => url_for_dir($cursor),
      current => ($i == $#segments) ? 1 : 0,
    };
  }

  return @breadcrumbs;
}

sub get_footer_nav {
  return unless (config_enabled($CONFIG{FOOTER_NAV}));

  my @nav = ({ label => "Back to top", href => "#content" });
  return @nav if (page_is_root());

  my $current = normalize_path($RUNTIME{logical_cwd});
  my $parent  = normalize_path(dirname($current));
  my $root    = normalize_path($RUNTIME{document_root});

  if ($parent ne $root) {
    push @nav, {
      label => title_for_dir($parent, ".."),
      href  => "..",
    };
  }

  push @nav, {
    label => $CONFIG{HOME_PAGE_TITLE},
    href  => "/",
  };

  return @nav;
}

sub get_title {
  return $CONFIG{PAGE_TITLE} if ($CONFIG{PAGE_TITLE});

  my $title = read_content_file_line($RUNTIME{logical_cwd}, $CONFIG{TITLE_FILE}, 1)
    || read_content_file_line($RUNTIME{logical_cwd}, $CONFIG{TOC_FILE}, 1);
  return $title if ($title);

  return $CONFIG{HOME_PAGE_TITLE} if (page_is_root());
  return $CONFIG{SITE_NAME} if ($CONFIG{SITE_NAME});
  return;
}

sub get_subtitle {
  return $CONFIG{PAGE_SUBTITLE} if ($CONFIG{PAGE_SUBTITLE});
  return read_content_file_line($RUNTIME{logical_cwd}, $CONFIG{TITLE_FILE}, 2);
}

sub get_intro {
  return $CONFIG{PAGE_INTRO} if ($CONFIG{PAGE_INTRO});
  return read_content_file($RUNTIME{logical_cwd}, $CONFIG{INTRO_FILE});
}

sub get_body {
  my @chunks;

  my $body_html = read_content_file($RUNTIME{logical_cwd}, $CONFIG{BODY_FILE});
  push @chunks, $body_html if (defined($body_html) && $body_html ne "");

  my $body_dir = content_file_path($RUNTIME{logical_cwd}, "body");
  if (-d $body_dir) {
    opendir(my $dh, $body_dir)
      or emit_error("Failed to read body fragment directory $body_dir: $!");
    my @fragments = sort grep { $_ !~ /^\./ && -f "${body_dir}/$_" } readdir($dh);
    closedir($dh);

    foreach my $fragment (@fragments) {
      my $content = read_text_file("${body_dir}/${fragment}");
      push @chunks, $content if (defined($content) && $content ne "");
    }
  }

  return unless (@chunks);
  return join("\n", @chunks);
}

sub get_toc_entry {
  my ($dir_path) = @_;
  return unless ($dir_path && -d $dir_path);

  my $info_path = content_file_path($dir_path, $CONFIG{TOC_FILE});
  return unless (-f $info_path);

  my $title = read_text_file_line($info_path, 1);
  return unless ($title);

  my $description = read_text_file($info_path);
  if (defined($description)) {
    my @parts = split(/\n/, $description, 2);
    $description = defined($parts[1]) ? $parts[1] : "";
    $description =~ s/^\s+//;
    $description =~ s/\s+$//;
  }

  return {
    title       => $title,
    path        => url_for_dir($dir_path) . "/",
    description => $description,
  };
}

sub get_toc {
  return unless (config_enabled($CONFIG{SHOW_TOC}));
  return unless (config_enabled($CONFIG{TREE_TOC}));

  opendir(my $dh, $RUNTIME{logical_cwd})
    or emit_error("Failed to read content directory $RUNTIME{logical_cwd}: $!");

  my @entries;
  foreach my $item (readdir($dh)) {
    next if ($item =~ /^\.\.?$/);
    my $path = content_file_path($RUNTIME{logical_cwd}, $item);
    next unless (-d $path);
    my $entry = get_toc_entry($path);
    push @entries, $entry if ($entry);
  }
  closedir($dh);

  @entries = sort { lc($a->{title}) cmp lc($b->{title}) } @entries;
  return @entries;
}

sub resolve_local_path {
  my ($path) = @_;
  return unless ($path);

  if ($path =~ m{^/}) {
    my $candidate = normalize_path(($RUNTIME{document_root} || "") . $path);
    return $candidate if ($candidate && -f $candidate);
  }

  my @search = grep { defined($_) && $_ ne "" } (
    $RUNTIME{logical_cwd},
    $RUNTIME{site_root},
    $RUNTIME{document_root},
  );

  foreach my $base (@search) {
    my $candidate = normalize_path("${base}/${path}");
    return $candidate if ($candidate && -f $candidate);
  }

  return;
}

# --------------------------------------------------------------------------- #
# /// Subelement assembly ///
# Build navigation, titles, body content, TOC data, and footer inputs from
# the resolved content directory and loaded configuration
# --------------------------------------------------------------------------- #

sub assemble_page {
  my @breadcrumbs = get_navigation();
  my @footer_nav = get_footer_nav();
  my @toc_entries = get_toc();

  return {
    current_url       => scalar(current_directory_url()),
    title             => scalar(get_title()),
    subtitle          => scalar(get_subtitle()),
    intro             => scalar(get_intro()),
    body              => scalar(get_body()),
    toc_entries       => \@toc_entries,
    breadcrumbs       => \@breadcrumbs,
    footer_nav        => \@footer_nav,
    nav_position      => navigation_position(),
    site_name         => $CONFIG{SITE_NAME},
    favicon           => $CONFIG{FAVICON},
    main_stylesheet   => $CONFIG{MAIN_STYLESHEET},
    legacy_stylesheet => $CONFIG{LEGACY_STYLESHEET},
    meta_description  => $CONFIG{PAGE_META_DESCRIPTION},
    meta_keywords     => $CONFIG{PAGE_META_KEYWORDS},
  };
}

sub navigation_position {
  my $position = defined($CONFIG{NAV_POSITION}) ? $CONFIG{NAV_POSITION} : "top";
  $position = lc($position);
  return "none" if ($position eq "none" || $position eq "0");
  return "bottom" if ($position eq "bottom" || $position eq "-1");
  return "top";
}

sub html_navigation {
  my ($page, $position) = @_;
  $position = "top" unless defined($position) && $position ne "";
  return unless ($page->{nav_position} eq $position);

  my @breadcrumbs = @{$page->{breadcrumbs}};
  return unless (@breadcrumbs);

  my @items;
  foreach my $crumb (@breadcrumbs) {
    my $item = $crumb->{label};
    $item = "<A HREF=\"$crumb->{href}\">$item</A>" unless ($crumb->{current});
    push @items, "<SPAN CLASS=\"breadcrumb_item\">${item}</SPAN>";
  }

  my $navigation = join($CONFIG{BREADCRUMB_SEPARATOR}, @items);
  return "<DIV ID=\"navigation\" CLASS=\"no_print\">\n${navigation}\n</DIV>\n";
}

sub html_title {
  my ($page) = @_;
  my $title = $page->{title};
  return unless ($title);
  return "<H1 ID=\"title\"><B>${title}</B></H1>\n";
}

sub html_subtitle {
  my ($page) = @_;
  my $subtitle = $page->{subtitle};
  return unless ($subtitle);
  return "<H2 ID=\"subtitle\">${subtitle}</H2>\n";
}

sub html_intro {
  my ($page) = @_;
  my $intro = $page->{intro};
  return unless ($intro);
  return "<DIV ID=\"intro\">\n${intro}\n</DIV>\n";
}

sub html_heading {
  my ($page) = @_;
  my $heading = "";
  $heading .= html_navigation($page, "top") || "";
  $heading .= html_title($page) || "";
  $heading .= html_subtitle($page) || "";
  $heading .= html_intro($page) || "";
  return $heading || undef;
}

sub html_toc {
  my ($page) = @_;
  my @entries = @{$page->{toc_entries}};
  return unless (@entries);

  my @items;
  foreach my $entry (@entries) {
    my $item = "<A HREF=\"$entry->{path}\">$entry->{title}</A>";
    $item = "<H3>${item}</H3>";
    $item .= "\n<P>$entry->{description}</P>" if ($entry->{description});
    push @items, "<LI>\n${item}\n</LI>\n";
  }

  my $toc = "<UL>\n" . join("", @items) . "</UL>\n";
  $toc = "<P>\n$CONFIG{TOC_SUBTITLE}</P>\n${toc}" if ($CONFIG{TOC_SUBTITLE});
  $toc = "<H2>$CONFIG{TOC_TITLE}</H2>\n${toc}" if ($CONFIG{TOC_TITLE});
  return "<DIV ID=\"contents\">\n${toc}</DIV>\n";
}

sub html_body {
  my ($page) = @_;
  my $body = $page->{body};
  my $toc  = html_toc($page);
  my @sections;

  push @sections, $body if ($body);
  if ($toc && (!$body || config_enabled($CONFIG{APPEND_TOC_TO_BODY}))) {
    push @sections, $toc;
  }

  return unless (@sections);
  return "<DIV ID=\"body\">\n" . join("\n", @sections) . "\n</DIV>\n";
}

sub html_footer_nav {
  my ($page) = @_;
  my @nav = @{$page->{footer_nav}};
  return unless (@nav);
  my @links = map { "<A HREF=\"$_->{href}\">$_->{label}</A>" } @nav;
  my $nav = join(" | ", @links);
  return "<SPAN CLASS=\"footer_navigation no_print\">${nav}</SPAN>";
}

sub html_footer {
  my ($page) = @_;
  my @footer = (scalar localtime());
  my $nav = html_footer_nav($page);
  push @footer, $nav if ($nav);
  @footer = grep { defined($_) && $_ ne "" } @footer;
  return unless (@footer);

  my @cells;
  for my $i (0 .. $#footer) {
    my $align = "left";
    $align = "right" if ($i == $#footer && $#footer > 0);
    $align = "center" if ($i > 0 && $i < $#footer);
    push @cells, "  <TD ALIGN=\"${align}\">$footer[$i]</TD>\n";
  }

  return "<TABLE WIDTH=\"100%\" CLASS=\"footer\">\n<TR>\n"
    . join("", @cells)
    . "</TR>\n</TABLE>\n";
}

# --------------------------------------------------------------------------- #
# /// HTML metadata assembly ///
# Build the <head> block and supporting asset references
# --------------------------------------------------------------------------- #

sub html_doctype {
  return "<!DOCTYPE $CONFIG{HTML_DOCTYPE}>\n";
}

sub html_meta_title {
  my ($page) = @_;
  my $title = $page->{title} || "";
  my $site_name = $page->{site_name} || "";

  $title =~ s/^\s+//;
  $title =~ s/\s+$//;
  $site_name =~ s/^\s+//;
  $site_name =~ s/\s+$//;

  $title = "" if ($site_name && $title && $site_name eq $title);
  my $page_title = "";
  $page_title .= $site_name if ($site_name);
  $page_title .= " - " if ($site_name && $title);
  $page_title .= $title if ($title);
  return "<TITLE>${page_title}</TITLE>\n" if ($page_title);
  return;
}

sub html_meta_style {
  my ($page) = @_;
  my $style = "";
  my $legacy_path = resolve_local_path($page->{legacy_stylesheet});
  if ($legacy_path) {
    my $legacy = read_text_file($legacy_path);
    if (defined($legacy) && $legacy ne "") {
      $style .= "<STYLE><!--\n${legacy}//--></STYLE>\n";
    }
  }

  $style .= "<LINK REL=\"stylesheet\" HREF=\"$page->{main_stylesheet}\">\n"
    if ($page->{main_stylesheet});
  return $style if ($style);
  return;
}

sub html_meta_favicon {
  my ($page) = @_;
  return "<LINK REL=\"icon\" TYPE=\"image/x-icon\" HREF=\"$page->{favicon}\">\n"
    if ($page->{favicon});
  return;
}

sub html_meta_description {
  my ($page) = @_;
  return "<META NAME=\"description\" CONTENT=\"$page->{meta_description}\">\n"
    if ($page->{meta_description});
  return;
}

sub html_meta_keywords {
  my ($page) = @_;
  return "<META NAME=\"keywords\" CONTENT=\"$page->{meta_keywords}\">\n"
    if ($page->{meta_keywords});
  return;
}

sub html_metadata {
  my ($page) = @_;
  my $metadata = "";
  $metadata .= html_meta_title($page) || "";
  $metadata .= html_meta_style($page) || "";
  $metadata .= html_meta_favicon($page) || "";
  $metadata .= html_meta_description($page) || "";
  $metadata .= html_meta_keywords($page) || "";
  return "<HEAD>\n${metadata}</HEAD>\n" if ($metadata);
  return;
}

# --------------------------------------------------------------------------- #
# /// Content assembly ///
# Compose the final page from assembled subelements in top-to-bottom order:
# heading, body, bottom navigation, footer, then wrap and emit
# --------------------------------------------------------------------------- #

sub html_content {
  my ($page) = @_;
  my $content = "";
  $content .= html_heading($page) || "";
  $content .= html_body($page) || "";
  $content .= html_navigation($page, "bottom") || "";
  $content .= html_footer($page) || "";
  return unless ($content);
  return "<BODY>\n<DIV ID=\"content\">\n${content}</DIV>\n</BODY>\n";
}

sub render_page {
  my $page = assemble_page();
  debug_line("content resolution", "Current URL path: $page->{current_url}");
  my $metadata = html_metadata($page) || "";
  my $body = html_content($page) || "";
  debug_line("render/output", "Emitting HTML response");

  my $content = "";
  $content .= content_header("text/html") if ($RUNTIME{mode} eq "cgi");
  $content .= html_doctype();
  $content .= "<HTML>\n";
  $content .= $metadata;
  $content .= debug_comment_block();
  $content .= $body;
  $content .= "</HTML>\n";
  return $content;
}

# --------------------------------------------------------------------------- #
# /// Execution pipeline ///
# Run the staged assembly process from runtime resolution through final output
# --------------------------------------------------------------------------- #

resolve_runtime();
my $output = render_page();
print $output;
