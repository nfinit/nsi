#!/usr/bin/perl
# NSI: The New Standard Index ----------------------------------------------- #
my $version = '3.0.0.9';
# --------------------------------------------------------------------------- #
$CONFIG_PATH = "res/config.conf";    # Site-wide default configuration
# --------------------------------------------------------------------------- #
# /// Dependencies ///                                                        
# --------------------------------------------------------------------------- #

use Cwd qw(getcwd abs_path);
use File::Basename qw(basename);

# --------------------------------------------------------------------------- #
# /// Utility subroutines ///
# --------------------------------------------------------------------------- #

sub read_file { # Read entire contents of a file
  my ($path) = @_;
  return unless (-f $path);
  open(my $fh, '<', $path) or return;
  my $content = do { local $/; <$fh> };
  close($fh);
  chomp($content) if ($content);
  return $content;
}

sub read_file_lines { # Read a range of file lines
  my ($path, $from, $to) = @_;
  return unless (-f $path);
  open(my $fh, '<', $path) or return;
  my @lines;
  my $n = 0;
  while (my $line = <$fh>) {
    $n++;
    next if ($n < $from);
    last if ($n > $to);
    chomp($line);
    push @lines, $line;
  }
  close($fh);
  return wantarray ? @lines : join("\n", @lines);
}

sub read_file_line { # Read a specific file line
  my ($path, $line_num) = @_;
  return read_file_lines($path, $line_num, $line_num);
}

# --------------------------------------------------------------------------- #
# /// Input mode handling ///
# --------------------------------------------------------------------------- #

sub content_header { # Generate CGI response header for a given content type
  my ($type) = @_;
  $type //= "text/html";
  return "Content-type: ${type}\n\n";
}

sub config_enabled { # Interpret common boolean config strings
  my ($value) = @_;
  return 0 unless defined($value);
  return 0 if ($value =~ /^(?:0|false|no|off)$/i);
  return 1 if ($value =~ /^(?:1|true|yes|on)$/i);
  return $value ? 1 : 0;
}

sub resolve_local_path { # Resolve site-relative asset path to a local file
  my ($path) = @_;
  return unless ($path);

  if ($path =~ m{^/}) {
    my $doc_root = $ENV{DOCUMENT_ROOT};
    return "${doc_root}${path}" if ($doc_root && -f "${doc_root}${path}");

    my $search_dir = Cwd::getcwd();
    while ($search_dir) {
      my $candidate = "${search_dir}${path}";
      return $candidate if (-f $candidate);
      last if ($search_dir eq "/");
      $search_dir =~ s{/[^/]+$}{};
      $search_dir = "/" if ($search_dir eq "");
    }
    return;
  }

  my $candidate = Cwd::getcwd() . "/" . $path;
  return $candidate if (-f $candidate);
  return;
}

# --------------------------------------------------------------------------- #
# /// Configuration loading ///
# --------------------------------------------------------------------------- #

sub get_config_value { # Load key from config file
  my ($key) = @_;
  return unless ($key && -f $CONFIG_PATH);
  open(my $fh, '<', $CONFIG_PATH) or return;
  while (my $line = <$fh>) {
    chomp($line);
    $line =~ s/^\s+|\s+$//g;
    next if ($line =~ /^#/ || $line eq "");
    if ($line =~ /^(\w+)\s*=\s*(.*)$/) {
      my ($k, $v) = ($1, $2);
      $v =~ s/\s+$//;
      if ($k eq $key) {
        close($fh);
        return $v;
      }
    }
  }
  close($fh);
  return;
}

sub read_config { # Set defaults and override with config values
  # Content file conventions (internal, not user-configurable)
  $TITLE_FILE = "title";
  $INTRO_FILE = "intro.html";
  $BODY_FILE  = "body.html";
  $TOC_FILE   = "info";

  # Display defaults
  $SITE_NAME        = "";
  $ORGANIZATION     = "";
  $NAV_POSITION     = "top";
  $BREADCRUMB_SEPARATOR = " &gt; ";
  $SHOW_TOC         = 1;
  $TREE_TOC         = 1;
  $TOC_TITLE        = "";
  $TOC_SUBTITLE     = "";
  $APPEND_TOC_TO_BODY = 1;
  $HOME_PAGE_TITLE = "Home";
  $FOOTER_NAV      = 1;
  $API_ENABLED     = 1;
  $DEBUG_TRACE     = 0;
  $FAVICON         = "/res/sys/favicon.ico";
  $SITE_STYLE_DIRECTORY = "/res/style";
  $MAIN_STYLESHEET = "${SITE_STYLE_DIRECTORY}/style.css";
  $LEGACY_STYLESHEET = "${SITE_STYLE_DIRECTORY}/legacy.css";
  $HTML_DOCTYPE    = 'HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"';

  # Output accumulators
  $CONTENT  = "";
  $METADATA = "";

  # Override from config file
  my $v;
  $SITE_NAME        = $v if ($v = get_config_value("site_name"));
  $ORGANIZATION     = $v if ($v = get_config_value("organization"));
  $NAV_POSITION     = $v if ($v = get_config_value("nav_position"));
  $BREADCRUMB_SEPARATOR = $v if ($v = get_config_value("breadcrumb_separator"));
  $SHOW_TOC         = $v if defined($v = get_config_value("show_toc"));
  $TREE_TOC         = $v if defined($v = get_config_value("tree_toc"));
  $TOC_TITLE        = $v if ($v = get_config_value("toc_title"));
  $TOC_SUBTITLE     = $v if ($v = get_config_value("toc_subtitle"));
  $APPEND_TOC_TO_BODY = $v if defined($v = get_config_value("append_toc_to_body"));
  $HOME_PAGE_TITLE = $v if ($v = get_config_value("home_page_title"));
  $FOOTER_NAV      = $v if ($v = get_config_value("footer_nav"));
  $API_ENABLED     = $v if defined($v = get_config_value("api_enabled"));
  $DEBUG_TRACE     = $v if defined($v = get_config_value("debug_trace"));
  $FAVICON         = $v if ($v = get_config_value("favicon"));
  $MAIN_STYLESHEET = $v if ($v = get_config_value("main_stylesheet"));
  $LEGACY_STYLESHEET = $v if ($v = get_config_value("legacy_stylesheet"));
  $SITE_STYLE_DIRECTORY = $v if ($v = get_config_value("site_style_directory"));

  # Per-page overrides (only set if present in config)
  $PAGE_TITLE            = $v if ($v = get_config_value("page_title"));
  $PAGE_SUBTITLE         = $v if ($v = get_config_value("page_subtitle"));
  $PAGE_INTRO            = $v if ($v = get_config_value("page_intro"));
  $PAGE_META_DESCRIPTION = $v if ($v = get_config_value("page_meta_description"));
  $PAGE_META_KEYWORDS    = $v if ($v = get_config_value("page_meta_keywords"));

  if ($SITE_STYLE_DIRECTORY) {
    $MAIN_STYLESHEET   = "${SITE_STYLE_DIRECTORY}/style.css"
      unless (get_config_value("main_stylesheet"));
    $LEGACY_STYLESHEET = "${SITE_STYLE_DIRECTORY}/legacy.css"
      unless (get_config_value("legacy_stylesheet"));
  }
}

read_config();

# --------------------------------------------------------------------------- #
# /// API handler ///
# --------------------------------------------------------------------------- #

# TODO: Reimplement simple API logic from v2

# --------------------------------------------------------------------------- #
# /// Client detection ///
# --------------------------------------------------------------------------- #

# TODO: Reimplement client detection tiering from v2

# --------------------------------------------------------------------------- #
# /// Subelement assembly ///
# Build content subelements from filesystem and configuration
# --------------------------------------------------------------------------- #

sub get_navigation() { # Get page navigation data
  my $current_dir = Cwd::getcwd();
  my $doc_root = $ENV{DOCUMENT_ROOT} // "";
  return unless ($doc_root);
  $current_dir =~ s/\/$//;
  $doc_root    =~ s/\/$//;
  return unless ($current_dir =~ /^\Q$doc_root\E(?:\/|$)/);
  return if ($current_dir eq $doc_root);

  my @breadcrumbs = ({
    label => $HOME_PAGE_TITLE // "Home",
    href => "/",
    current => 0,
  });

  my $relative_path = $current_dir;
  $relative_path =~ s/^\Q$doc_root\E\/?//;
  my @segments = split(/\//, $relative_path);

  my $cumulative_path = $doc_root;
  for (my $i = 0; $i < @segments; $i++) {
    my $segment = $segments[$i];
    next unless ($segment);
    $cumulative_path .= "/$segment";

    my $href = $cumulative_path;
    $href =~ s/^\Q$doc_root\E//;
    $href = "/" if ($href eq "");

    push @breadcrumbs, {
      label => get_title_for_path($cumulative_path, $segment),
      href => $href,
      current => ($i == $#segments) ? 1 : 0,
    };
  }

  return @breadcrumbs;
}

sub meditate() { # Get a random "meditation" image path
  return;
}

sub get_title() { # Get page display title from configuration or content
  return $PAGE_TITLE if ($PAGE_TITLE);
  return read_file_line($TITLE_FILE, 1) || read_file_line($TOC_FILE, 1);
}

sub get_subtitle() { # Get page subtitle from configuration or content
  return $PAGE_SUBTITLE if ($PAGE_SUBTITLE);
  return read_file_line($TITLE_FILE, 2);
  # We don't reference TOC_FILE here because an external subtitle
  # isn't necessarily suitable for the page itself, use a title file instead
}

sub get_intro() { # Get page intro from configuration or content
  return $PAGE_INTRO if ($PAGE_INTRO);
  return read_file($INTRO_FILE);
}

sub get_body() { # Assemble body from content
  my @body_chunks;
  # Get a static body file if it exists
  if (-f $BODY_FILE) {
    my $body_file = read_file($BODY_FILE);
    push @body_chunks, $body_file if defined($body_file) && $body_file ne "";
  }
  # Body fragment directory
  if (-d "body") {
    unless (opendir(my $dh, "body")) {
      return join("\n", @body_chunks) if (@body_chunks);
      return;
    }
    my @fragments = sort grep { -f "body/$_" && $_ !~ /^\./ } readdir($dh);
    closedir($dh);
    foreach my $fragment (@fragments) {
      my $fragment_content = read_file("body/$fragment");
      push @body_chunks, $fragment_content
        if defined($fragment_content) && $fragment_content ne "";
    }
  }
  return join("\n", @body_chunks) if (@body_chunks);
  return;
}

sub get_toc_entry { # Get TOC entry data for a directory
  my ($dir_path) = @_;
  return unless ($dir_path && -d $dir_path);
  my $info_path = "${dir_path}/${TOC_FILE}";
  return unless (-f $info_path);

  my $title = read_file_line($info_path, 1);
  return unless defined($title) && $title ne "";

  my $description = read_file($info_path);
  if (defined($description)) {
    my @parts = split(/\n/, $description, 2);
    $description = $parts[1] // "";
    $description =~ s/^\s+|\s+$//g;
  }

  my $path = $dir_path;
  $path =~ s#^\./##;
  $path .= "/" unless ($path =~ /\/$/);

  return {
    title => $title,
    path => $path,
    description => $description,
    fs_path => $dir_path,
  };
}

sub get_toc { # Get table of contents data
  return unless (config_enabled($SHOW_TOC));
  return unless (config_enabled($TREE_TOC));
  my $dh;
  unless (opendir($dh, ".")) {
    return;
  }

  my @entries;
  foreach my $item (readdir($dh)) {
    next if ($item =~ /^\.\.?$/);
    next unless (-d $item);
    my $entry = get_toc_entry($item);
    push @entries, $entry if ($entry);
  }
  closedir($dh);

  @entries = sort {
    lc($a->{title}) cmp lc($b->{title})
  } @entries;
  return @entries;
}

sub get_title_for_path { # Get title for an arbitrary directory path
  my ($dir_path, $fallback) = @_;
  $fallback //= "";
  return $fallback unless ($dir_path);
  $dir_path =~ s/\/$//;
  # Title file, then TOC file, then directory basename
  return read_file_line("${dir_path}/${TITLE_FILE}", 1)
      || read_file_line("${dir_path}/${TOC_FILE}", 1)
      || basename($dir_path)
      || $fallback;
}

sub get_footer_nav { # Get footer navigation links as raw data
  my @nav;
  my $current_dir = Cwd::getcwd();
  my $doc_root = $ENV{DOCUMENT_ROOT} // "";
  $current_dir =~ s/\/$//;
  $doc_root    =~ s/\/$//;
  my $at_root = ($current_dir eq $doc_root);
  # Back to top is always present
  push @nav, { label => "Back to top", href => "#content" };
  # Parent link if not at root and parent isn't root
  if (!$at_root && Cwd::abs_path("..") ne Cwd::abs_path($doc_root)) {
    push @nav, { label => get_title_for_path("..", ".."), href => ".." };
  }
  # Home link if not at root
  if (!$at_root) {
    push @nav, { label => $HOME_PAGE_TITLE // "Home", href => "/" };
  }
  return @nav;
}

sub get_footer() { # Assemble footer from configuration
  my @footer;
  push @footer, scalar localtime();
  return @footer;
}

# HTML heading assembly #######################################################

sub navigation_position() { # Normalize navigation position setting
  my $position = lc($NAV_POSITION // "top");
  return "none" if ($position eq "none" || $position eq "0");
  return "bottom" if ($position eq "bottom" || $position eq "-1");
  return "top";
}

sub html_navigation { # Generate page navigation element
  my ($position) = @_;
  $position //= "top";
  return unless (navigation_position() eq $position);

  my @breadcrumbs = get_navigation();
  return unless (@breadcrumbs);

  my @items;
  foreach my $crumb (@breadcrumbs) {
    my $item = $crumb->{label};
    $item = "<A HREF=\"$crumb->{href}\">$item</A>" unless ($crumb->{current});
    push @items, "<SPAN CLASS=\"breadcrumb_item\">${item}</SPAN>";
  }

  my $separator = $BREADCRUMB_SEPARATOR // " &gt; ";
  my $navigation = join($separator, @items);
  return "<DIV ID=\"navigation\" CLASS=\"no_print\">\n${navigation}\n</DIV>\n";
}

sub html_meditate() { # HTML wrapper for meditation
  my $meditation;
  $meditation = "<IMG ID=\"meditation\" SRC=\"" . $meditation . "\">"
    if ($meditation = meditate());
  return($meditation);
}

sub html_title() { # HTML wrapper for title
  my $title;
  $title = "<H1 ID=\"title\"><B>" . $title . "</B></H1>" if ($title = get_title());
  return($title);
}

sub html_subtitle() { # HTML wrapper for subtitle
  my $subtitle;
  return($subtitle);
}

sub html_intro() { # HTML wrapper for intro
  my $intro;
  $intro = "<DIV ID=\"intro\">\n" . $intro . "\n</DIV>" if ($intro = get_intro());
  return($intro);
}

sub html_heading() { # Generate HTML header/title element
  my $heading, $medtitation, $title, $intro, $navigation;
  $heading .= $navigation if ($navigation = html_navigation("top"));
  $heading .= $meditation if ($meditation = html_meditate());
  $heading .= $title if ($title = html_title());
  $heading .= $subtitle if ($subtitle = html_subtitle());
  $heading .= $intro if ($intro = html_intro());
  return($heading);
}

# HTML body assembly ##########################################################

sub html_body() { # HTML wrapper for body content
  my $body = get_body();
  my $toc = html_toc();
  my @main_sections;

  push @main_sections, $body if ($body);
  if ($toc && (!$body || config_enabled($APPEND_TOC_TO_BODY))) {
    push @main_sections, $toc;
  }

  return unless (@main_sections);
  return "<DIV ID=\"body\">\n" . join("\n", @main_sections) . "\n</DIV>\n";
}

# HTML footer assembly ########################################################

sub html_footer_nav { # Generate footer navigation HTML from raw nav data
  return unless (config_enabled($FOOTER_NAV));
  my @nav = get_footer_nav();
  return unless (@nav);
  my @links = map { "<A HREF=\"$_->{href}\">$_->{label}</A>" } @nav;
  my $nav = join(" | ", @links);
  return "<SPAN CLASS=\"footer_navigation no_print\">${nav}</SPAN>";
}

sub html_footer() {
  my @footer = get_footer();
  my $nav = html_footer_nav();
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

  my $footer = "<TABLE WIDTH=\"100%\" CLASS=\"footer\">\n";
  $footer .= "<TR>\n";
  $footer .= join("", @cells);
  $footer .= "</TR>\n";
  $footer .= "</TABLE>\n";
  return $footer;
}

# HTML metadata assembly ###################################################### 

sub html_toc { # HTML wrapper for table of contents
  my @entries = get_toc();
  return unless (@entries);

  my @items;
  foreach my $entry (@entries) {
    my $item = "<A HREF=\"$entry->{path}\">$entry->{title}</A>";
    $item = "<H3>${item}</H3>";
    $item .= "\n<P>$entry->{description}</P>" if ($entry->{description});
    push @items, "<LI>\n${item}\n</LI>\n";
  }

  my $toc = "<UL>\n" . join("", @items) . "</UL>\n";
  $toc = "<P>\n${TOC_SUBTITLE}</P>\n${toc}" if ($TOC_SUBTITLE);
  $toc = "<H2>${TOC_TITLE}</H2>\n${toc}" if ($TOC_TITLE);
  return "<DIV ID=\"contents\">\n${toc}</DIV>\n";
}

sub html_doctype() { # Set HTML DOCTYPE based on client detection
  my $doctype = $HTML_DOCTYPE // 'HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"';
  return "<!DOCTYPE ${doctype}>\n";
}

sub html_meta_title() { # Get page title from parsed data 
  my $title = get_title();
  my $site_name = $SITE_NAME;

  if (defined($title)) {
    $title =~ s/^\s+|\s+$//g;
  }
  if (defined($site_name)) {
    $site_name =~ s/^\s+|\s+$//g;
  }

  if ($site_name && $title && $site_name eq $title) {
    $title = "";
  }

  my $page_title = "";
  $page_title .= $site_name if ($site_name);
  $page_title .= " - " if ($site_name && $title);
  $page_title .= $title if ($title);
  return "<TITLE>${page_title}</TITLE>\n" if ($page_title);
  return;
}

sub html_meta_style() { # Get page style block
  my $style = "";
  my $legacy_path = resolve_local_path($LEGACY_STYLESHEET);
  if ($legacy_path && open(my $style_fh, '<', $legacy_path)) {
    $style .= "<STYLE><!--\n";
    while (my $line = <$style_fh>) {
      $style .= $line;
    }
    close($style_fh);
    $style .= "//--></STYLE>\n";
  }
  $style .= "<LINK REL=\"stylesheet\" HREF=\"${MAIN_STYLESHEET}\">\n"
    if ($MAIN_STYLESHEET);
  return $style if ($style);
  return;
}

sub html_meta_favicon() { # Get favicon if available
  return "<LINK REL=\"icon\" TYPE=\"image/x-icon\" HREF=\"${FAVICON}\">\n" if ($FAVICON);
  return;
}

sub html_meta_description() { # Get page description from config or content
  return "<META NAME=\"description\" CONTENT=\"${PAGE_META_DESCRIPTION}\">\n" if ($PAGE_META_DESCRIPTION);
  return;
}

sub html_meta_keywords() { # Get page keywords from config or content
  return "<META NAME=\"keywords\" CONTENT=\"${PAGE_META_KEYWORDS}\">\n" if ($PAGE_META_KEYWORDS);
  return;
}

sub html_metadata() { # Get page metadata (<head> block)
  my $metadata = "";
  $metadata .= html_meta_title();
  $metadata .= html_meta_style();
  $metadata .= html_meta_favicon();
  $metadata .= html_meta_description();
  $metadata .= html_meta_keywords();
  $metadata .= $METADATA if ($METADATA);
  return "<HEAD>\n${metadata}</HEAD>\n" if ($metadata);
  return;
}

# --------------------------------------------------------------------------- #
# /// Subelement transformation ///
# Transform domain-specific NSI extensions in raw input markup 
# to standard/expanded format in sequential order per domain based on
# contents of extension directory
# --------------------------------------------------------------------------- #

sub transform_html_header { # Transform HTML header with markup extensions
  my $header = $_[0];
  return $header; 
}

sub transform_html_body { # Transform HTML body with markup extensions
  my $body = $_[0];
  return $body; 
}

sub transform_html_footer { # Transform HTML footer with markup extensions
  my $footer = $_[0];
  return $footer; 
}

sub html_content() { # Compose all visible HTML content (header, body, footer)
  my $content;
  $content .= transform_html_header(html_heading());
  $content .= transform_html_body(html_body());
  $content .= transform_html_header(html_navigation("bottom"));
  $content .= transform_html_footer(html_footer());
  $content = "<BODY>\n<DIV ID=\"content\">\n${content}</DIV>\n</BODY>\n" if ($content);
  return $content;
}

# --------------------------------------------------------------------------- #
# /// Content assembly ///
# Assemble and emit final response to client from subelements
# --------------------------------------------------------------------------- #

$CONTENT .= content_header();
$CONTENT .= html_doctype();
$CONTENT .= "<HTML>\n";
$CONTENT .= html_metadata();
$CONTENT .= html_content();
$CONTENT .= "</HTML>\n";

# --------------------------------------------------------------------------- #
print $CONTENT if ($CONTENT);
# --------------------------------------------------------------------------- #
