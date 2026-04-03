#!/usr/bin/perl
# NSI: The New Standard Index ----------------------------------------------- #
my $version = '3.0.0.0';
# --------------------------------------------------------------------------- #
$CONFIG_PATH = "res/config.conf";    # Site-wide default configuration
# --------------------------------------------------------------------------- #
# /// Dependencies ///                                                        
# --------------------------------------------------------------------------- #

# TODO: Setup standard library imports

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

# --------------------------------------------------------------------------- #
# /// Configuration loading ///
# --------------------------------------------------------------------------- #

sub get_config_value() { # Load key from config file
  return;
}

sub read_config() { # Set defaults and override with config values
  return;
}

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
  return;
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
  my $body = "";
  # Get a static body file if it exists 
  $body .= read_file($BODY_FILE) if (-f $BODY_FILE);
  # Body fragment directory
  if (-d "body") {
    opendir(my $dh, "body") or return $body;
    my @fragments = sort grep { -f "body/$_" && $_ !~ /^\./ } readdir($dh);
    closedir($dh);
    foreach my $fragment (@fragments) {
      $body .= read_file("body/$fragment");
    }
  }
  return $body if ($body);
  return;
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

sub html_navigation() { # Generate page navigation element
  return;
}

sub html_meditate() { # HTML wrapper for meditation
  my $meditation;
  $meditation = "<img id=\"meditation\" src=\"" . $meditation . "\">"
    if ($meditation = meditate());
  return($meditation);
}

sub html_title() { # HTML wrapper for title
  my $title;
  $title = "<h1 id=\"title\">" . $title . "</h1>" if ($title = get_title());
  return($title);
}

sub html_subtitle() { # HTML wrapper for subtitle
  my $subtitle;
  return($subtitle);
}

sub html_intro() { # HTML wrapper for intro
  my $intro;
  $intro = "<p id=\"intro\">" . $intro . "</p>" if ($intro = get_intro());
  return($intro);
}

sub html_heading() { # Generate HTML header/title element
  my $heading, $medtitation, $title, $intro, $navigation;
  $heading .= $navigation if ($navigation = html_navigation());
  $heading .= $meditation if ($meditation = html_meditate());
  $heading .= $title if ($title = html_title());
  $heading .= $subtitle if ($subtitle = html_subtitle());
  $heading .= $intro if ($intro = html_intro());
  return($heading);
}

# HTML body assembly ##########################################################

sub html_body() {
  return;
}

# HTML footer assembly ########################################################

sub html_footer_nav { # Generate footer navigation HTML from raw nav data
  return unless ($FOOTER_NAV);
  my @nav = get_footer_nav();
  return unless (@nav);
  my @links = map { "<a href=\"$_->{href}\">$_->{label}</a>" } @nav;
  return join(" | ", @links);
}

sub html_footer() {
  my @footer = get_footer();
  my $nav = html_footer_nav();
  push @footer, $nav if ($nav);
  return @footer;
}

# HTML metadata assembly ###################################################### 

sub html_doctype() { # Set HTML DOCTYPE based on client detection
  my $doctype = $HTML_DOCTYPE // 'HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"';
  return "<!DOCTYPE ${doctype}>\n";
}

sub html_meta_title() { # Get page title from parsed data 
  return;
}

sub html_meta_style() { # Get page style block
  return;
}

sub html_meta_favicon() { # Get favicon if available
  return "<link rel=\"icon\" TYPE=\"image/x-icon\" href=\"${FAVICON}\">\n" if ($FAVICON);
  return;
}

sub html_meta_description() { # Get page description from config or content
  return "<meta name=\"description\" content=\"${PAGE_META_DESCRIPTION}\">\n" if ($PAGE_META_DESCRIPTION);
  return;
}

sub html_meta_keywords() { # Get page keywords from config or content
  return "<meta name=\"description\" content=\"${PAGE_META_KEYWORDS}\">\n" if ($PAGE_META_KEYWORDS);
  return;
}

sub html_metadata() { # Get page metadata (<head> block)
  my $metadata;
  $metadata .= html_meta_title(); 
  $metadata .= html_meta_style();
  $metadata .= html_meta_favicon(); 
  $metadata .= html_meta_description();
  $metadata .= html_meta_keywords();
  $metadata .= "<head>\n${METADATA}</head>\n" if ($metadata);
  return($metadata);
}

# --------------------------------------------------------------------------- #
# /// Subelement transformation ///
# Transform domain-specific NSI extensions in raw input markup 
# to standard/expanded format in sequential order per domain based on
# contents of extension directory
# --------------------------------------------------------------------------- #

sub transform_html_header() { # Transform HTML header with markup extensions
  my $header = $_[0];
  return $header; 
}

sub transform_html_body() { # Transform HTML body with markup extensions
  my $body = $_[0];
  return $body; 
}

sub transform_html_footer() { # Transform HTML footer with markup extensions
  my $footer = $_[0];
  return $footer; 
}

sub html_content() { # Compose all visible HTML content (header, body, footer)
  my $content;
  $content .= transform_html_header(html_header());
  $content .= transform_html_body(html_body());
  $content .= transform_html_footer(html_footer());
  $content = "<body>\n${content}</body>\n" if ($content);
  return $content;
}

# --------------------------------------------------------------------------- #
# /// Content assembly ///
# Assemble and emit final response to client from subelements
# --------------------------------------------------------------------------- #

$CONTENT .= content_header();
$CONTENT .= html_doctype();
$CONTENT .= "<html>\n";
$CONTENT .= html_metadata();
$CONTENT .= html_content();
$CONTENT .= "</html>\n";

# --------------------------------------------------------------------------- #
print $CONTENT if ($CONTENT);
# --------------------------------------------------------------------------- #
