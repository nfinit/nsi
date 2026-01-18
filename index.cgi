#!/usr/bin/perl
# NSI: The New Standard Index for simple websites --------------------------- #
my $version = '2.19.0.1';
# --------------------------------------------------------------------------- #

$_SITE_CONFIG_NAME = "res/config.pl";
$_LOCAL_CONFIG = "./.config.pl";

# =========================================================================== #
use utf8;
use Cwd qw(cwd abs_path);
use File::Basename;
use Time::HiRes qw(time);
# --------------------------------------------------------------------------- #
# Variables that can be set in config.pl or local .config.pl
# All have sensible defaults - see "Configuration defaults" section below
# --------------------------------------------------------------------------- #
use vars qw(
$MEDITATE
$PAGE_TITLE $PAGE_INTRO
$HTML_DOCTYPE $CLOUDFLARE
$NAV_POSITION $FOOTER_NAV $BREADCRUMB_SEPARATOR
$CENTER_TITLE $AUTO_RULE $SUB_LOGO $TREE_TOC $WRAP_SCRIPT_OUTPUT
$CENTER_IMAGE_CAPTIONS
$SHOW_TOC $TOC_TITLE $TOC_SUBTITLE $APPEND_TOC_TO_BODY
$EXPAND_GROUPS $EXPAND_GROUPS_DEPTH
$BODY_FILE $TITLE_FILE $INTRO_FILE $TOC_FILE $GROUP_FILE
$LOGO $FAVICON
$RESOURCE_DIRECTORY $STYLE_DIRECTORY
$IMAGE_DIRECTORY $API_IMAGE_DIRECTORY $PREVIEW_DIRECTORY
$LEGACY_PREVIEW_DIRECTORY $LEGACY_PREVIEW_STANDARD_DIRECTORY
$COLLAGE_THUMBNAIL_DIRECTORY $FULLSIZE_IMAGE_DIRECTORY
$SITE_RESOURCE_DIRECTORY $SITE_SYSRES_DIRECTORY
$SITE_IMAGE_DIRECTORY $SITE_STYLE_DIRECTORY $SITE_MEDITATION_DIRECTORY
$PREVIEW_WIDTH $LEGACY_PREVIEW_WIDTH $COLLAGE_THUMBNAIL_WIDTH
$IMAGE_API_RECURSE $API_ENABLED
$MEDITATION_DIRECTORY
$MAIN_STYLESHEET $LEGACY_STYLESHEET
$HOSTNAME $ORGANIZATION $SITE_NAME $HOME_PAGE_TITLE $CURRENT_TIME
$LINE_ELEMENTS $LINE_ELEMENT_DIVIDER $LINE_FRAME_L $LINE_FRAME_R
$DEBUG_TRACE
);
# Set run mode -------------------------------------------------------------- #
my $_WWW_EXEC;
my $_INTERACTIVE;
$_WWW_EXEC = 1 if ($ENV{GATEWAY_INTERFACE} || $ENV{REQUEST_METHOD});
$_INTERACTIVE = 1 if (!$_WWW_EXEC) and (-t STDERR);
# Configuration processing -------------------------------------------------- #
# In web context, use logical path (preserving symlinks via SCRIPT_NAME)
# In CLI context, use physical path (cwd)
my $search_path;
if ($_WWW_EXEC && $ENV{SCRIPT_NAME}) {
    # Extract directory from script path to preserve symlink semantics
    my $script_dir = $ENV{SCRIPT_NAME};
    $script_dir =~ s/\/[^\/]+$//;  # Remove /index.cgi or script name
    $script_dir = "/" if (!$script_dir);  # Handle root case
    $search_path = $ENV{DOCUMENT_ROOT} . $script_dir;
} else {
    # CLI mode: use physical path
    $search_path = cwd();
}

while ($search_path ne '/') {
    my $potential_config = "$search_path/$_SITE_CONFIG_NAME";
    if (-f $potential_config) {
        $_SITE_CONFIG = $potential_config;
        last;
    }
    $search_path = dirname($search_path);
}

if (!$_SITE_CONFIG) {
    $SITE_CONFIG_ERRORS++;
    $SITE_ERROR_TEXT = "Site configuration file ($_SITE_CONFIG_NAME) not found in any parent directory.";
}

if (-f $_SITE_CONFIG && !do $_SITE_CONFIG) { $SITE_CONFIG_ERRORS++; }
$SITE_ERROR_TEXT .= $@ if ($SITE_CONFIG_ERRORS);
if (-f $_LOCAL_CONFIG && !do $_LOCAL_CONFIG) { $LOCAL_CONFIG_ERRORS++; }
$LOCAL_ERROR_TEXT .= $@ if ($LOCAL_CONFIG_ERRORS);
$CONFIG_ERRORS = $SITE_CONFIG_ERRORS + $LOCAL_CONFIG_ERRORS;
if ($CONFIG_ERRORS) {
  print  "Content-type: text/html\n\n";
  print "<strong>";
  print "<p>Error reading site configuration file</p>\n" 
	if ($CONFIG_ERRORS);
  print "</strong>\n";
  if ($SITE_ERROR_TEXT || $LOCAL_ERROR_TEXT) {
    print "<p>The following error text was returned:</p>\n";
    print "<pre>${SITE_ERROR_TEXT}</pre>";
    print "<pre>${LOCAL_ERROR_TEXT}</pre>";
  } else {
    print "<p>No error text was returned by the server.<p>\n";
    print "<p>Last configuration block completed: ${CONFIG_BLOCK}</p>"
	if ($CONFIG_BLOCK);
  }
  exit;
}
$MASTER_CONFIG_INIT = 1;

# Configuration defaults ---------------------------------------------------- #
# These apply if not set in config.pl. Override by setting in your config.

# Site identity
$HOSTNAME       //= `hostname -s`;
$CURRENT_TIME   //= scalar localtime();
$ORGANIZATION   //= "";
$SITE_NAME      //= "";
$HOME_PAGE_TITLE //= "Home";

# Display behavior
$NAV_POSITION      //= 1;   # 1=top, -1=bottom, 0=none
$FOOTER_NAV        //= 1;
$BREADCRUMB_SEPARATOR //= " &gt; ";
$CENTER_TITLE      //= 0;
$AUTO_RULE         //= 1;
$SUB_LOGO          //= 0;
$WRAP_SCRIPT_OUTPUT //= 0;
$CENTER_IMAGE_CAPTIONS //= 1;

# Table of contents
$SHOW_TOC            //= 1;
$TREE_TOC            //= 1;
$TOC_TITLE           //= "";
$TOC_SUBTITLE        //= "";
$APPEND_TOC_TO_BODY  //= 1;
$EXPAND_GROUPS       //= 1;
$EXPAND_GROUPS_DEPTH //= 1;

# Content files (new names, with legacy dotfile fallback)
$TITLE_FILE //= "title";
$INTRO_FILE //= "intro.html";
$BODY_FILE  //= "body.html";
$TOC_FILE   //= "info";
$GROUP_FILE //= "group";

# Resource paths (derived from $RESOURCE_DIRECTORY)
$RESOURCE_DIRECTORY //= "res";
$STYLE_DIRECTORY    //= "${RESOURCE_DIRECTORY}/style";
$IMAGE_DIRECTORY    //= "${RESOURCE_DIRECTORY}/img";
$FULLSIZE_IMAGE_DIRECTORY  //= "${IMAGE_DIRECTORY}/full";
$PREVIEW_DIRECTORY         //= "${IMAGE_DIRECTORY}/previews";
$LEGACY_PREVIEW_DIRECTORY  //= "${PREVIEW_DIRECTORY}/legacy";
$LEGACY_PREVIEW_STANDARD_DIRECTORY //= "${LEGACY_PREVIEW_DIRECTORY}/standard";
$COLLAGE_THUMBNAIL_DIRECTORY       //= "${LEGACY_PREVIEW_DIRECTORY}/collage";
$MEDITATION_DIRECTORY //= "${IMAGE_DIRECTORY}/meditations";

# Site-relative paths (for URLs)
$SITE_RESOURCE_DIRECTORY   //= "/res";
$SITE_SYSRES_DIRECTORY     //= "${SITE_RESOURCE_DIRECTORY}/sys";
$SITE_IMAGE_DIRECTORY      //= "${SITE_RESOURCE_DIRECTORY}/img";
$SITE_STYLE_DIRECTORY      //= "${SITE_RESOURCE_DIRECTORY}/style";
$SITE_MEDITATION_DIRECTORY //= "${SITE_IMAGE_DIRECTORY}/meditations";

# Resources
$FAVICON           //= "${SITE_SYSRES_DIRECTORY}/favicon.ico";
$LOGO              //= "${SITE_SYSRES_DIRECTORY}/logo.gif";
$MAIN_STYLESHEET   //= "${SITE_STYLE_DIRECTORY}/style.css";
$LEGACY_STYLESHEET //= "${SITE_STYLE_DIRECTORY}/legacy.css";

# Image processing
$PREVIEW_WIDTH           //= 1024;
$LEGACY_PREVIEW_WIDTH    //= 600;
$COLLAGE_THUMBNAIL_WIDTH //= 300;
$IMAGE_API_RECURSE       //= 1;

# Metadata
$HTML_DOCTYPE //= 'HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"';
$CLOUDFLARE   //= 0;

# System features
$API_ENABLED    //= 1;
$DEBUG_TRACE    //= 0;

# Line elements (display formatting)
$LINE_ELEMENTS        //= 1;
$LINE_ELEMENT_DIVIDER //= " | ";
$LINE_FRAME_L         //= "[ ";
$LINE_FRAME_R         //= " ]";

# Preprocessing block ------------------------------------------------------- #

chomp $HOSTNAME;


# Utility subroutines ------------------------------------------------------- #

# Resolve content file path with legacy dotfile fallback
# Returns path that exists, preferring new name over legacy
sub resolve_content_file {
	my ($dir, $filename) = @_;
	$dir //= ".";
	my $new_path = "${dir}/${filename}";
	return $new_path if -f $new_path;
	
	# Legacy fallback: .title, .intro, .info, .group
	my $legacy_name = $filename;
	$legacy_name =~ s/^(title|info|group)$/.$1/;
	$legacy_name =~ s/^intro\.html$/.intro/;
	
	my $legacy_path = "${dir}/${legacy_name}";
	return $legacy_path if -f $legacy_path;
	
	return $new_path;  # Default to new path if neither exists
}

# Use to mark sensitive data blocks
# (i.e. for hiding from bad actors using Cloudflare)
sub secure_data {
	my $html = shift @_;
	return "<!--sse-->\n${html}<!--/sse-->\n" if ($CLOUDFLARE);
	return $html;
}

# Extract relative subdirectory path by removing base directory prefix
# Used to derive structure from config variables (e.g., "full" from "res/img/full")
sub get_relative_subdir {
	my ($base_dir, $full_path) = @_;
	return "" unless ($base_dir && $full_path);

	my $relative = $full_path;
	# Remove base directory prefix, handling trailing slashes
	$base_dir =~ s/\/$//;
	$relative =~ s/^\Q$base_dir\E\/?//;
	return $relative;
}

# Get legacy preview path with backward compatibility
# Checks new semantic structure first, falls back to old flat structure
# Automatically migrates files from old to new location on access (silent migration)
# Returns the path that exists, or new path if neither exists (for new images)
sub get_legacy_preview_path {
	my $basename = shift @_;

	# Check new semantic location (preferred)
	my $new_path = "${LEGACY_PREVIEW_STANDARD_DIRECTORY}/${basename}.gif";
	return $new_path if (-f $new_path);

	# Check old flat location (backward compatibility)
	my $old_path = "${LEGACY_PREVIEW_DIRECTORY}/${basename}.gif";
	if (-f $old_path) {
		# Silent migration: Move file to new semantic structure
		# Create directory if needed
		unless (-d $LEGACY_PREVIEW_STANDARD_DIRECTORY) {
			mkdir($LEGACY_PREVIEW_STANDARD_DIRECTORY);
		}

		# Attempt migration
		if (rename($old_path, $new_path)) {
			debug_line("Silently migrated legacy preview: ${basename}.gif");
			return $new_path;
		} else {
			# Migration failed, return old path (still works)
			debug_line("Failed to migrate legacy preview: ${basename}.gif - $!");
			return $old_path;
		}
	}

	# Neither exists - return new path (will be created during processing)
	return $new_path;
}

# Find image by basename, searching both processed and unprocessed locations
# Searches with priority: processed images first, then unprocessed fallback
# Returns: ($full_path, $extension, $is_processed)
#   $full_path: Full filesystem path to the image file
#   $extension: File extension (jpg, png, gif, etc.)
#   $is_processed: 1 if from processed directory (has previews), 0 if unprocessed
sub find_image_by_basename {
	my ($basename, $search_base) = @_;
	return (undef, undef, 0) unless $basename;

	# Default search base to IMAGE_DIRECTORY if not specified
	$search_base = $IMAGE_DIRECTORY unless $search_base;

	# Extract relative structure from config to apply to search base
	my $fullsize_subdir = get_relative_subdir($IMAGE_DIRECTORY, $FULLSIZE_IMAGE_DIRECTORY);
	my $local_fullsize_dir = $fullsize_subdir ? "${search_base}/${fullsize_subdir}" : "${search_base}/full";

	my @extensions = ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif');

	# Priority 1: Check processed images in full/ subdirectory
	if (-d $local_fullsize_dir) {
		foreach my $ext (@extensions) {
			my $test_file = "${local_fullsize_dir}/${basename}.${ext}";
			if (-f $test_file) {
				debug_line("Found processed image: ${test_file}");
				return ($test_file, $ext, 1);
			}
		}
	}

	# Priority 2: Check unprocessed images in base directory
	foreach my $ext (@extensions) {
		my $test_file = "${search_base}/${basename}.${ext}";
		if (-f $test_file) {
			debug_line("Found unprocessed image: ${test_file}");
			return ($test_file, $ext, 0);
		}
	}

	# Not found
	return (undef, undef, 0);
}

# Preformat text and assign an id if provided 
sub preformat_text {
	my $text = shift @_;
	return if (!$text);
	return "<PRE CLASS=\"script-output\">\n${text}</PRE>\n";
}

my $_DEBUG_TRACE_LINES;
sub debug_line {
	my $line = shift @_;
	return if (!$DEBUG_TRACE);
	return if (!$line);
	$trace_line = "[" . time . "] ${line}\n";
  if ($_INTERACTIVE) {
	  print STDERR $trace_line;
  } else {
	  $_DEBUG_TRACE_LINES .= $trace_line;
  } 
	return;
}
debug_line("*** DEBUG TRACE ***");
debug_line("NSI ${version}");
debug_line("uid: $>");
debug_line("gids: $)");
debug_line("Current working directory is '" . cwd() . "'");
debug_line("Running in interactive mode.") if ($_INTERACTIVE);
debug_line("API is enabled.") if ($API_ENABLED);
debug_line("Query string: $ENV{'QUERY_STRING'}") if ($ENV{'QUERY_STRING'});

# Browser detection subroutines --------------------------------------------- #
# Provides client browser detection and tier classification for feature
# adaptation. Returns tier levels (legacy/midtier/modern) that can be used
# to adjust rendering, image sizes, and other browser-specific behaviors.
#
# User-Agent detection is inherently imperfect and should be used sparingly.
# NSI philosophy: Default to assuming capability, only detect when absolutely
# necessary for compatibility (e.g., known broken behavior in specific browsers).
#
# USAGE:
#   In web context, $_BROWSER_TIER is automatically set to 'legacy', 'midtier',
#   or 'modern'. Use this variable to conditionally adjust behavior:
#
#   Example:
#     my $img_dir = ($_BROWSER_TIER eq 'legacy')
#                   ? $COLLAGE_THUMBNAIL_DIRECTORY
#                   : $PREVIEW_DIRECTORY;
#
#   To add new browser detection:
#     1. Create a helper function (e.g., sub is_browsername)
#     2. Add logic to get_browser_tier() for tier classification
#     3. Update this documentation

# Detect if client is Netscape Navigator 4.x
# Pattern: Mozilla/4.x WITHOUT "compatible", "MSIE", or "Gecko"
# Modern browsers spoof Mozilla/4 but include identifying keywords
sub is_netscape4 {
	my $ua = $ENV{HTTP_USER_AGENT} || '';
	return 1 if ($ua =~ /Mozilla\/4\./ && $ua !~ /compatible|MSIE|Gecko/i);
	return 0;
}

# Detect Internet Explorer and return major version number
# Returns version (4, 5, 6, etc.) or 0 if not IE
sub get_ie_version {
	my $ua = $ENV{HTTP_USER_AGENT} || '';
	return $1 if ($ua =~ /MSIE (\d+)\./);
	return 0;
}

# Detect Opera browser and return major version number
# Returns version or 0 if not Opera
sub get_opera_version {
	my $ua = $ENV{HTTP_USER_AGENT} || '';
	return $1 if ($ua =~ /Opera[\/\s](\d+)/i);
	return 0;
}

# Main browser tier detection function
# Returns: 'legacy', 'midtier', or 'modern'
#
# legacy  - Browsers with known broken behavior requiring special handling
#           (NN4, IE4-5, extremely limited CSS/JS support)
# midtier - Older but functional browsers (IE6-9, Opera 4-9, early Firefox)
#           Decent CSS support, limited modern features
# modern  - Current browsers and unknowns (assume capability)
#           Full CSS3, modern standards
sub get_browser_tier {
	# Tier 1: Legacy browsers with known limitations
	return 'legacy' if (is_netscape4());

	my $ie_ver = get_ie_version();
	return 'legacy' if ($ie_ver >= 4 && $ie_ver <= 5);

	# Tier 2: Mid-tier browsers (functional but dated)
	return 'midtier' if ($ie_ver >= 6 && $ie_ver <= 9);

	my $opera_ver = get_opera_version();
	return 'midtier' if ($opera_ver >= 4 && $opera_ver <= 9);

	# Tier 3: Modern browsers (default for unknowns)
	# Better to assume capability than to break on new browsers
	return 'modern';
}

# Detect browser tier for this request (only in web context)
my $_BROWSER_TIER;
if (!$_INTERACTIVE) {
	$_BROWSER_TIER = get_browser_tier();
	debug_line("Browser tier: ${_BROWSER_TIER}");
	debug_line("User-Agent: $ENV{HTTP_USER_AGENT}") if ($ENV{HTTP_USER_AGENT});
}

# Generic dynamic content subroutines --------------------------------------- #

# Automatic content rule
sub auto_hr {
  return "<HR CLASS=\"divider\">\n" if ($AUTO_RULE);
}

# Meditate
sub meditate {
  my $meditation;
  return if (! -d $MEDITATION_DIRECTORY);
  opendir(MEDITATIONS,$MEDITATION_DIRECTORY) or die $!;
  my @meditations = grep { -f "$MEDITATION_DIRECTORY/$_" && $_ !~ /^\./ } readdir(MEDITATIONS);
  closedir(MEDITATIONS);
  my $meditation_count = scalar @meditations;
  return if (!$meditation_count);
  my $selection = int(rand($meditation_count));
  $meditation = "$MEDITATION_DIRECTORY/$meditations[$selection]";
  $meditation = "<IMG SRC=\"${meditation}\" CLASS=\"meditation\">\n";
  return($meditation);
}

sub process_body_fragments {
	my $body_dir = "body";
	return "" if (! -d $body_dir);

	my $fragment_content = "";

	# Open directory and get all files (not subdirectories)
	opendir(my $body_dh, $body_dir) or return "";
	my @fragments = grep { -f "$body_dir/$_" && $_ !~ /^\./ } readdir($body_dh);
	closedir($body_dh);

	# Sort alphabetically (numeric prefixes like 01-, 02- will sort naturally)
	@fragments = sort @fragments;

	foreach my $fragment (@fragments) {
		my $fragment_path = "$body_dir/$fragment";

		# Check if fragment is executable script (must have shebang)
		my $is_script = 0;
		if (-x $fragment_path) {
			if (open(my $check_fh, '<', $fragment_path)) {
				my $first_line = <$check_fh>;
				close($check_fh);
				$is_script = 1 if ($first_line && $first_line =~ /^#!/);
			}
		}

		if ($is_script) {
			# Check for per-script WRAP override on line 2
			my $wrap_output = $WRAP_SCRIPT_OUTPUT;  # Default to global setting
			if (open(my $script_fh, '<', $fragment_path)) {
				my $line1 = <$script_fh>;  # Shebang line
				my $line2 = <$script_fh>;  # Potential override comment
				close($script_fh);
				if ($line2) {
					$wrap_output = 1 if ($line2 =~ /^\s*#\s*WRAP\s*$/i);
					$wrap_output = 0 if ($line2 =~ /^\s*#\s*NO\s*WRAP\s*$/i);
				}
			}

			# Execute script and capture output
			my $script_output = `./$fragment_path 2>&1`;
			if ($script_output) {
				# Optionally wrap script output in <pre> tags
				if ($wrap_output) {
					$fragment_content .= "<PRE>\n${script_output}</PRE>\n";
				} else {
					$fragment_content .= $script_output;
				}
			}
		} else {
			# Read static HTML fragment
			if (open(my $fh, '<', $fragment_path)) {
				local $/;
				my $file_content = <$fh>;
				close($fh);
				$fragment_content .= $file_content if ($file_content);
			}
		}
	}

	return $fragment_content;
}

# Transform <nsi-banner> tags into styled banner blocks
# Usage: <nsi-banner class="warning" title="Notice">Description text</nsi-banner>
# Classes: info, warning, note (or any custom class for CSS)
sub transform_nsi_banner_tags {
	my $content = shift @_;
	return $content if (!$content);
	$content =~ s{<nsi-banner\s+([^>]*)>(.*?)</nsi-banner>}{
		my $attrs = $1;
		my $description = $2;
		my $class = ($attrs =~ /class="([^"]*)"/) ? $1 : 'info';
		my $title = ($attrs =~ /title="([^"]*)"/) ? $1 : '';
		my $out = "<DIV CLASS=\"nsi-banner nsi-banner-${class}\">\n";
		$out .= "  <B>${title}</B>\n" if ($title);
		$out .= "  <P>${description}</P>\n" if ($description);
		$out .= "</DIV>\n";
		$out;
	}geis;
	return $content;
}

sub transform_nsi_image_tags {
	my $content = shift @_;
	return $content if (!$content);

	# Find all <img nsi-res="..."> tags with optional alt and caption attributes
	$content =~ s{<img\s+([^>]*nsi-res="[^"]+"[^>]*)\s*/?>}{
		my $attrs = $1;
		my $replacement = "";

		# Extract nsi-res attribute (required)
		my $basename = "";
		if ($attrs =~ /nsi-res="([^"]+)"/) {
			$basename = $1;
		}

		# Extract optional alt attribute
		my $alt_text = "";
		if ($attrs =~ /alt="([^"]*)"/) {
			$alt_text = $1;
		} else {
			$alt_text = $basename;  # Default to basename
		}

		# Extract optional caption attribute
		my $caption = "";
		if ($attrs =~ /caption="([^"]*)"/) {
			$caption = $1;
		}

		# Search for image in both processed and unprocessed locations
		my ($found_file, $found_ext, $is_processed) = find_image_by_basename($basename, $IMAGE_DIRECTORY);

		if ($found_file) {
			# Build the replacement HTML
			my $full_path = $found_file;

			if ($is_processed) {
				# Processed image: has previews available
				# Use legacy previews (600px GIF) for legacy browsers, standard previews (1024px) for others
				# Legacy previews are always GIF format for maximum compatibility
				# Backward compatible: checks both new semantic structure and old flat structure
				my $preview_path = ($_BROWSER_TIER eq 'legacy')
				                   ? get_legacy_preview_path($basename)
				                   : "${PREVIEW_DIRECTORY}/${basename}.${found_ext}";

				$replacement = "<DIV CLASS=\"nsi-image\">\n";
				$replacement .= "  <A HREF=\"${full_path}\">\n";
				$replacement .= "    <IMG SRC=\"${preview_path}\" ALT=\"${alt_text}\">\n";
				$replacement .= "  </A>\n";
			} else {
				# Unprocessed image: no previews, serve original directly
				$replacement = "<DIV CLASS=\"nsi-image\">\n";
				$replacement .= "  <A HREF=\"${full_path}\">\n";
				$replacement .= "    <IMG SRC=\"${full_path}\" ALT=\"${alt_text}\">\n";
				$replacement .= "  </A>\n";
			}

			# Add caption if provided (applies to both processed and unprocessed)
			if ($caption) {
				if ($CENTER_IMAGE_CAPTIONS) {
					$replacement .= "  <CENTER><P CLASS=\"nsi-caption\">${caption}</P></CENTER>\n";
				} else {
					$replacement .= "  <P CLASS=\"nsi-caption\">${caption}</P>\n";
				}
			}

			$replacement .= "</DIV>\n";
		} else {
			# Image not found - show error
			$replacement = "<!-- NSI: Image '${basename}' not found in processed or unprocessed directories -->\n";
			$replacement .= "<I>[Image: ${basename} (not found)]</I>";
		}

		$replacement;
	}gei;

	return $content;
}

sub transform_nsi_collage_tags {
	my $content = shift @_;
	return $content if (!$content);

	# Find all <div nsi-collage="..."> blocks and transform them
	# NOTE: Case-sensitive to avoid matching uppercase </DIV> tags from nsi-image blocks
	$content =~ s{<div\s+nsi-collage="([^"]+)"[^>]*>(.*?)</div>}{
		my $layout = $1;
		my $inner_content = $2;
		my $replacement = "";

		# Extract all nsi-image DIVs from the content
		my @images;
		while ($inner_content =~ /<DIV\s+CLASS="nsi-image">(.*?)<\/DIV>/gis) {
			push @images, $1;
		}

		# Return original if no images found
		$& if (!@images);

		# Add WIDTH="100%" to IMG tags for broader browser compatibility.
		# While NN4 ignores this, many other period browsers (IE5+, Opera, etc.)
		# do respect it. Combined with CSS (modern) and CSS expressions (IE5),
		# this provides the widest compatibility.
		foreach my $img (@images) {
			$img =~ s/<IMG\s+/<IMG WIDTH="100%" /gi;
		}

		# For legacy browsers in collages, use smaller collage thumbnails (300px)
		# instead of standard legacy previews (600px) for better fit
		if ($_BROWSER_TIER eq 'legacy') {
			foreach my $img (@images) {
				# Replace legacy preview paths with collage thumbnail paths
				# Handles both old flat structure and new semantic structure
				$img =~ s{/previews/legacy/standard/([^/]+)\.gif}{/previews/legacy/collage/$1.gif}g;
				$img =~ s{/previews/legacy/([^/]+)\.gif}{/previews/legacy/collage/$1.gif}g;
			}
		}

		# Determine layout type and build table
		if ($layout eq 'horizontal') {
			# Single row layout with equal-width cells
			my $num_images = scalar @images;
			my $cell_width = int(100 / $num_images);

			$replacement = "<TABLE WIDTH=\"100%\" CLASS=\"nsi-collage nsi-horizontal\">\n<TR>\n";
			foreach my $img (@images) {
				$replacement .= "  <TD WIDTH=\"${cell_width}%\" CLASS=\"nsi-collage-cell\">\n${img}  </TD>\n";
			}
			$replacement .= "</TR>\n</TABLE>\n";

		} elsif ($layout =~ /^grid-(\d+)$/) {
			# Grid layout with specified columns
			my $columns = $1;
			my $cell_width = int(100 / $columns);

			$replacement = "<TABLE WIDTH=\"100%\" CLASS=\"nsi-collage nsi-grid-${columns}\">\n";

			my $col = 0;
			foreach my $img (@images) {
				$replacement .= "<TR>\n" if ($col == 0);
				$replacement .= "  <TD WIDTH=\"${cell_width}%\" CLASS=\"nsi-collage-cell\">\n${img}  </TD>\n";
				$col++;

				if ($col >= $columns) {
					$replacement .= "</TR>\n";
					$col = 0;
				}
			}

			# Close incomplete row if needed
			if ($col > 0) {
				# Fill remaining cells with empty TDs for alignment
				while ($col < $columns) {
					$replacement .= "  <TD WIDTH=\"${cell_width}%\" CLASS=\"nsi-collage-cell-empty\"></TD>\n";
					$col++;
				}
				$replacement .= "</TR>\n";
			}

			$replacement .= "</TABLE>\n";

		} else {
			# Unknown layout type - return original
			$&;
		}

		$replacement;
	}ges;

	return $content;
}

sub get_logical_cwd {
	# Get current working directory preserving symlink semantics
	# For web requests, construct from SCRIPT_NAME to preserve logical path
	# For CLI, use physical cwd()

	if ($ENV{SCRIPT_NAME}) {
		# Extract directory from script path (e.g., /galleries/travel/index.cgi -> /galleries/travel)
		my $script_dir = $ENV{SCRIPT_NAME};
		$script_dir =~ s/\/[^\/]+$//;  # Remove /index.cgi or script name
		$script_dir = "/" if (!$script_dir);  # Handle root case

		# Construct absolute filesystem path
		return $ENV{DOCUMENT_ROOT} . $script_dir;
	}

	# Fallback to physical path for non-web contexts
	return cwd();
}

# Get title for a specific directory path
# Checks title file, then info file (first line), then returns fallback
sub get_title_for_path {
	my ($dir_path, $fallback) = @_;
	$fallback //= "";
	return $fallback unless $dir_path;

	# Normalize path
	$dir_path =~ s/\/$//;

	# Check for title file
	my $title_file = resolve_content_file($dir_path, $TITLE_FILE);
	if (-f $title_file) {
		if (open(my $fh, '<', $title_file)) {
			my $title = <$fh>;
			close($fh);
			chomp($title) if ($title);
			return $title if ($title);
		}
	}

	# Check for info file (first line)
	my $info_file = resolve_content_file($dir_path, $TOC_FILE);
	if (-f $info_file) {
		if (open(my $fh, '<', $info_file)) {
			my $title = <$fh>;
			close($fh);
			chomp($title) if ($title);
			return $title if ($title);
		}
	}

	# Fallback to directory name if no explicit fallback given
	if (!$fallback) {
		my $dir_name = basename($dir_path);
		return $dir_name if $dir_name;
	}

	return $fallback;
}

sub get_parent_title {
	# Resolve parent directory path
	my $parent_dir;

	if ($ENV{SCRIPT_NAME}) {
		my $script_dir = $ENV{SCRIPT_NAME};
		$script_dir =~ s/\/[^\/]+$//;  # Remove /index.cgi
		if ($script_dir =~ m|^(.*)/[^/]+$|) {
			my $parent_url_path = $1 || "/";
			$parent_dir = $ENV{DOCUMENT_ROOT} . $parent_url_path;
		}
	}
	$parent_dir //= "..";

	return get_title_for_path($parent_dir, "..");
}

sub get_page_title {
  my $title = "";
  my $resolved_title_file = resolve_content_file(".", $TITLE_FILE);
  my $resolved_toc_file = resolve_content_file(".", $TOC_FILE);

  # Title precedence: config override > title file > info file > site defaults
  if ($PAGE_TITLE) { 
    $title = "${PAGE_TITLE}"; 
  } elsif ( -f $resolved_title_file ) {
    open(my $title_html, '<', $resolved_title_file)
      or die "Cannot open static content file $resolved_title_file";
    { 
      local $/;
      $title = <$title_html>;
    }
    close(title_html);
  } elsif ( -f $resolved_toc_file ) {
    # Fallback to first line of info file if no explicit title
    open(my $info_fh, '<', $resolved_toc_file);
    if ($info_fh) {
      my $info_title = <$info_fh>;
      close($info_fh);
      chomp($info_title) if ($info_title);
      $title = $info_title if ($info_title);
    }
  }

  # Final fallback to site defaults
  if (!$title) {
    my $current_dir = get_logical_cwd();
    my $doc_root = $ENV{DOCUMENT_ROOT};
    $current_dir =~ s/\/$//;
    $doc_root =~ s/\/$//;

    if ($current_dir eq $doc_root) {
      $title = $HOME_PAGE_TITLE;
    } elsif ($SITE_NAME) {
      $title = $SITE_NAME;
    } elsif ($HOSTNAME || $ORGANIZATION) {
      $title .= "${HOSTNAME}"     if ($HOSTNAME);
      $title .= " @ "             if ($HOSTNAME && $ORGANIZATION);
      $title .= "${ORGANIZATION}" if ($ORGANIZATION);
    }
  }
  return ($title);
}

# Page title
sub page_title {
  my $title = get_page_title();
  return if (!$title);
  $title = "<H1><B>${title}</B></H1>" if ($title);
  if ($LOGO && (cwd() eq $ENV{DOCUMENT_ROOT} 
      || (cwd() ne $ENV{DOCUMENT_ROOT} 
      && $SUB_LOGO))) {
    $logo_src .= "<TD><IMG SRC=\"${LOGO}\"></TD>";
    $title = "<TD>${title}</TD>";
    $title = "<TABLE><TR>\n${logo_src}\n${title}\n</TR></TABLE>\n";
  }
  if ($MEDITATE) {
    $title = meditate() . $title;
  }
  $title = "<CENTER>\n${title}</CENTER>\n" if ($CENTER_TITLE);
  return($title);
}

sub page_intro {
  my $intro = "";
  my $resolved_intro_file = resolve_content_file(".", $INTRO_FILE);
  if ($PAGE_INTRO) 
  { 
    $intro .= "${PAGE_INTRO}"; 
  } elsif ( -f $resolved_intro_file ) {
    open(my $intro_html, '<', $resolved_intro_file)
      or die "Cannot open static content file $resolved_intro_file";
    { 
      local $/;
      $intro = <$intro_html>;
    }
    close(intro_html);
  }
  $intro = "<DIV ID=\"intro\">\n${intro}\n</DIV>" if ($intro);
  $intro = auto_hr() . $intro if ($intro); 
  return($intro);
}

# Table of Contents subroutines --------------------------------------------- #

# TREE TOC
# --------
# Generate a table of contents array for a specified directory tree using
# files as defined by the $TOC_FILE variable for titles and descriptions
# Array structure: [0]=title, [1]=path, [2]=description, [3]=is_group, [4]=group_title_override, [5]=fs_path
sub tree_toc {
	my @TOC;
	my $target_directory = shift;
	$target_directory = '.' if !$target_directory;
	if (opendir(ROOT,"${target_directory}")) {
		my @contents = grep !/^.\.*$/, readdir(ROOT);
		closedir(ROOT);
		foreach $item (@contents) {
			$item = $target_directory . '/' . $item;
			if (-d $item) {
				my $item_data = resolve_content_file($item, $TOC_FILE);
				if (-f $item_data) {
					my @item_array;
					my $item_title;
					my $item_path = "${item}/";
					$item_path =~ s/^$ENV{DOCUMENT_ROOT}//;
					my $item_description;
					my $is_group = 0;
					my $group_title_override;
					if (open(ITEM_DATA,$item_data)) {
						my $data_line = 0;
						while (<ITEM_DATA>) {
							$item_title = "$_" if (!$data_line);
							$item_description .= "$_" if ($data_line);
							$data_line++;
						}
						close(ITEM_DATA);
					}
					# Check for .group flag file
					my $item_group = resolve_content_file($item, $GROUP_FILE);
					if (-f $item_group) {
						$is_group = 1;
						if (open(ITEM_GROUP, $item_group)) {
							my $override = <ITEM_GROUP>;
							chomp $override if $override;
							$group_title_override = $override if $override;
							close(ITEM_GROUP);
						}
					}
					push @item_array, $item_title;
					push @item_array, $item_path;
					push @item_array, $item_description;
					push @item_array, $is_group;
					push @item_array, $group_title_override;
					push @item_array, $item;  # filesystem path for expansion
					push (@TOC, \@item_array) if ($item_title && $item_path);
				}
			}
		}
	}
	@TOC = sort { $a->[0] cmp $b->[0] } @TOC;
	return (@TOC);
}

# FILE TOC
# --------
# TBD

# UNIFIED TOC
# -----------
# Generate a single TOC at the given location 
# with all applicable methods
sub toc {
	my @TOC;
	my ($target_directory) = @_;
	$target_directory = '.' if (!$target_directory);
	push(@TOC,tree_toc("${target_directory}")) if ($TREE_TOC);
	return if (!@TOC);
	return (@TOC);
}

# PAGE TOC
# ----------
sub page_toc {
	return if (!$SHOW_TOC);
	my @TOC = toc();
	return if (!@TOC);
	my $contents = render_toc_list(\@TOC, 1);
	return if (!$contents);
	$contents = "<UL>\n${contents}</UL>\n";
	$contents = "<P>\n${TOC_SUBTITLE}</P>\n${contents}" if ($TOC_SUBTITLE);
	$contents = "<H2>${TOC_TITLE}</H2>\n${contents}" if ($TOC_TITLE);
	$contents = "<DIV ID=\"contents\">\n${contents}</DIV>\n";
	$contents = auto_hr() . $contents;
	return ($contents);
}

# Render TOC list items, with optional group expansion
# $depth tracks current recursion level for EXPAND_GROUPS_DEPTH
sub render_toc_list {
	my ($toc_ref, $depth) = @_;
	my $contents = '';
	foreach my $toc_link (@$toc_ref) {
		my $item_name        = $toc_link->[0];
		my $item_path        = $toc_link->[1];
		my $item_description = $toc_link->[2];
		my $is_group         = $toc_link->[3];
		my $group_title      = $toc_link->[4];
		my $fs_path          = $toc_link->[5];
		next if (!$item_name || !$item_path);
		
		my $display_title = $group_title || $item_name;
		my $list_item = "<A HREF=\"${item_path}\">${display_title}</A>";
		$list_item = "<H3>${list_item}</H3>";
		$list_item .= "\n<P>${item_description}</P>" if ($item_description);
		
		# Expand group if enabled and within depth limit
		if ($is_group && $EXPAND_GROUPS && $depth <= $EXPAND_GROUPS_DEPTH) {
			# Get group's intro content
			my $group_intro = get_file_content($fs_path, $INTRO_FILE);
			$list_item .= "\n${group_intro}" if ($group_intro);
			# Only show body if no description in info file
			if (!$item_description) {
				my $group_body = get_file_content($fs_path, $BODY_FILE);
				$list_item .= "\n${group_body}" if ($group_body);
			}
			# Get group's nested TOC
			my @sub_toc = tree_toc($fs_path);
			if (@sub_toc) {
				my $sub_contents = render_toc_list(\@sub_toc, $depth + 1);
				$list_item .= "\n<UL>\n${sub_contents}</UL>" if ($sub_contents);
			}
		}
		
		$contents .= "<LI>\n${list_item}\n</LI>\n";
	}
	return $contents;
}

# Get content from a file in a directory (for group expansion)
sub get_file_content {
	my ($dir, $filename) = @_;
	my $file = resolve_content_file($dir, $filename);
	return '' unless -f $file;
	open(my $fh, '<', $file) or return '';
	local $/;
	my $content = <$fh>;
	close($fh);
	return $content;
}

# Navigation subroutines ~~~~~~~--------------------------------------------- #

sub cwd_nested_in {
	my $target_directory = shift; # Get first argument
	return if !$target_directory;
  $target_directory =~ /\/$/;
  my $current_directory = get_logical_cwd();
  $current_directory =~ /\/$/;
  $current_directory =~ s/^$ENV{DOCUMENT_ROOT}//;
  $target_directory  =~ s/^$ENV{DOCUMENT_ROOT}//;
  return $current_directory =~ /^$target_directory/;
}

sub navigation_menu {
	return if (!$NAV_POSITION);

	# Normalize paths for comparison (handle trailing slash differences)
	my $current_dir = get_logical_cwd();
	my $doc_root = $ENV{DOCUMENT_ROOT};
	$current_dir =~ s/\/$//;
	$doc_root =~ s/\/$//;

	# Skip navigation at root - just "Home" is pointless
	return if ($current_dir eq $doc_root);

	# Build breadcrumb trail from root to current location
	my @breadcrumbs;

	# Always start with Home
	push @breadcrumbs, {
		title => $HOME_PAGE_TITLE,
		path => '/',
		is_current => ($current_dir eq $doc_root)
	};

	# If not at root, build path segments
	if ($current_dir ne $doc_root) {
		# Get relative path from root
		my $relative_path = $current_dir;
		$relative_path =~ s/^\Q$doc_root\E\/?//;

		# Split into segments
		my @segments = split(/\//, $relative_path);

		# Build cumulative path and create breadcrumb for each segment
		my $cumulative_path = $doc_root;
		for (my $i = 0; $i < @segments; $i++) {
			my $segment = $segments[$i];
			next unless $segment;  # Skip empty segments

			$cumulative_path .= "/$segment";
			my $url_path = $cumulative_path;
			$url_path =~ s/^\Q$doc_root\E//;
			$url_path = '/' if (!$url_path);

			# Get title for this segment
			my $title = get_title_for_path($cumulative_path);
			$title = $segment unless $title;  # Fallback to directory name

			# Check if this is the current page
			my $is_current = ($i == $#segments);

			push @breadcrumbs, {
				title => $title,
				path => $url_path,
				is_current => $is_current
			};
		}
	}

	# Build HTML for breadcrumbs
	my $menu = "";
	for (my $i = 0; $i < @breadcrumbs; $i++) {
		my $crumb = $breadcrumbs[$i];
		my $item = "";

		# Add separator before all items except the first
		if ($i > 0) {
			$item .= $BREADCRUMB_SEPARATOR;
		}

		# Current page: plain text (no link)
		if ($crumb->{is_current}) {
			$item .= $crumb->{title};
		} else {
			# Other pages: linked
			$item .= "<A HREF=\"$crumb->{path}\">$crumb->{title}</A>";
		}

		$item = "<SPAN CLASS=\"breadcrumb_item\">${item}</SPAN>";
		$menu .= $item;
	}

	# Wrap in navigation div with horizontal rule before
	$menu = "<DIV ID=\"navigation\" CLASS=\"no_print\">\n${menu}\n</DIV>\n";
	$menu = auto_hr() . $menu;
	return ($menu);
}

# Footer subroutines -------------------------------------------------------- #

sub page_footer {
	my $footer = "<!-- PAGE FOOTER -->\n";
	my $footer_row;
	my $footer_left;
	my $footer_right;
	# Content in the LEFT ALIGNED block
	# Page generation timestamp
	my $timestamp = "<SPAN CLASS=\"timestamp\">";
	$timestamp .= $LINE_FRAME_L if ($LINE_ELEMENTS);
	$timestamp .= $CURRENT_TIME;
	$timestamp .= $LINE_FRAME_R if ($LINE_ELEMENTS);
	$timestamp .= "</SPAN>\n";
	$footer_left .= "${timestamp}";
	$footer_left = "<TD ALIGN=\"LEFT\">${footer_left}</TD>\n";
	$footer_row .= $footer_left;
	# Content in the RIGHT ALIGNED block
	if ($FOOTER_NAV) {
		my $footer_nav;
		my $nav_controls = "";

		# Normalize paths for comparison (handle trailing slash differences)
		my $current_dir = get_logical_cwd();
		my $doc_root = $ENV{DOCUMENT_ROOT};
		$current_dir =~ s/\/$//;
		$doc_root =~ s/\/$//;
		my $at_root = ($current_dir eq $doc_root);

		# Check if parent is root using logical path
		my $parent_is_root = (abs_path("..") eq abs_path($ENV{DOCUMENT_ROOT}));

		# Add "Back to top" link as the first element
		$nav_controls .= "<A HREF=\"#content\">Back to top</A>\n";
		# Add divider after if there will be more controls
		if (!$at_root) {
			$nav_controls .= $LINE_ELEMENT_DIVIDER if ($LINE_ELEMENTS);
		}

		# Only show parent link if not at root and parent is not the root
		if (!$at_root && !$parent_is_root) {
			my $parent_title = get_parent_title();
			$nav_controls .= "<A HREF=\"..\">${parent_title}</A>\n";
			$nav_controls .= $LINE_ELEMENT_DIVIDER if ($LINE_ELEMENTS);
		}

		# Show Home link if not at root
		if (!$at_root) {
			$nav_controls .= "<A HREF=\"/\">${HOME_PAGE_TITLE}</A>\n";
		}

		# Only render the footer navigation block if there are controls
		if ($nav_controls) {
			$footer_nav .= "<SPAN CLASS=\"footer_navigation no_print\">\n";
			$footer_nav .= $LINE_FRAME_L if ($LINE_ELEMENTS);
			$footer_nav .= $nav_controls;
			$footer_nav .= $LINE_FRAME_R if ($LINE_ELEMENTS);
			$footer_nav .= "</SPAN>\n";
			$footer_right .= $footer_nav;
		}
	}	
	$footer_right = "<TD ALIGN=\"RIGHT\">${footer_right}</TD>\n";
	$footer_row .= $footer_right;
	$footer_row = "<TR>\n${footer_row}</TR>\n";
	$footer .= "<TABLE WIDTH=\"100%\" CLASS=\"footer\">\n";
	$footer .= $footer_row;
	$footer .= "</TABLE>\n";
	$footer = auto_hr() . $footer;
	return($footer);
}

# Metadata subroutines ------------------------------------------------------ #

# Metadata title
sub metadata_title {
  my $page_title;
  my $title = get_page_title();
  if (!$SITE_NAME) {
    $SITE_NAME  = "${HOSTNAME}"     if ($HOSTNAME);
    $SITE_NAME .= " @ "             if ($ORGANIZATION && $HOSTNAME);
    $SITE_NAME .= "${ORGANIZATION}" if ($ORGANIZATION);
  }
  # Clean whitespace from both for comparison
  my $clean_title = $title;
  my $clean_site = $SITE_NAME;
  $clean_title =~ s/^\s+|\s+$//g if $clean_title;
  $clean_site =~ s/^\s+|\s+$//g if $clean_site;
  # Deduplicate: if page title equals site name, don't repeat it
  $title = '' if ($clean_site && $clean_title && $clean_site eq $clean_title);
  $page_title .= "${SITE_NAME}" if ($SITE_NAME);
  $page_title .= " - "          if ($SITE_NAME && $title);
  $page_title .= "${title}"     if ($title);
  $page_title  = $META_TITLE    if ($META_TITLE);
  return if (!$page_title);
  $page_title = "<TITLE>${page_title}</TITLE>\n";
  return($page_title);
}

# Metadata stylesheet
sub metadata_style {
  my $style;
  if ($LEGACY_STYLESHEET && substr($LEGACY_STYLESHEET,0,1) eq '/') {
  	$LEGACY_STYLESHEET = $ENV{DOCUMENT_ROOT} . $LEGACY_STYLESHEET;
  } else {
	$LEGACY_STYLESHEET = cwd() . '/' . $LEGACY_STYLESHEET;
  }
  if (-f $LEGACY_STYLESHEET && open(STYLE,$LEGACY_STYLESHEET)) {
    $style .= "<STYLE><!--\n";
    $style .= "$_" while (<STYLE>);
    $style .= "//--></STYLE>\n";
  }
  if ($MAIN_STYLESHEET)
  { $style .= "<LINK REL=\"stylesheet\" HREF=\"${MAIN_STYLESHEET}\">\n"; }
  return($style);
}

# Metadata block
sub generate_metadata {
  my $metadata;
  $metadata .= metadata_title();
  $metadata .= metadata_style();
  $metadata .= "<LINK REL=\"icon\" TYPE=\"image/x-icon\" HREF=\"${FAVICON}\">\n"
               if ($FAVICON);
  $metadata .= "<META NAME=\"description\" CONTENT=\"${META_DESCRIPTION}\">\n"
               if ($META_DESCRIPTION);
  $metadata .= "<META NAME=\"keywords\" CONTENT=\"${META_KEYWORDS}\">\n"
               if ($META_KEYWORDS);
  return($metadata);
}

# Media subroutines --------------------------------------------------------- #

# Process driver for page preview generation
sub process_page_images {
    debug_line("Entering subroutine: process_page_images()");
    debug_line("Target image directory is '${IMAGE_DIRECTORY}'");
    my $img_dir = $IMAGE_DIRECTORY;
    debug_line("No image directory for this page, skipping...") unless -d $img_dir;
    return unless -d $img_dir;
    
    # Create subdirectories if they don't exist
    my @subdirs = (
        $FULLSIZE_IMAGE_DIRECTORY,
        $PREVIEW_DIRECTORY,
        $LEGACY_PREVIEW_DIRECTORY,
        $LEGACY_PREVIEW_STANDARD_DIRECTORY,
        $COLLAGE_THUMBNAIL_DIRECTORY
    );
    foreach my $dir (@subdirs) {
	debug_line("Check for subdirectory: ${dir}");
        mkdir($dir) or debug_line("Attempt to create required directory '${dir}' failed: $!") and return
       		unless -d $dir;
    }
    
    # Move loose files to fullsized folder and generate previews
    debug_line("Checking for loose files in '${img_dir}'...");
    opendir(my $dh, $img_dir) or return;
    my @loose_files = grep {
        -f "$img_dir/$_" && /\.(jpg|jpeg|png|gif|bmp|tiff?)$/i
    } readdir($dh);
    closedir($dh);
    debug_line("Found " . scalar @loose_files . " loose file(s).");

    my $processed_count = 0;

    foreach my $file (@loose_files) {
	debug_line("Moving lose file '${file}' to '${FULLSIZE_IMAGE_DIRECTORY}' for processing...");
        my $source = "$img_dir/$file";
        my $dest = "$FULLSIZE_IMAGE_DIRECTORY/$file";

        # Move to fullsize directory if not already there
        if (rename($source, $dest)) {
            generate_image_previews($dest, $file);
            print "." if ($_INTERACTIVE);  # Progress indicator
            $processed_count++;
        }
    }

    # Scan fullsize directory for images missing previews
    debug_line("Scanning fullsize directory for images with missing previews...");
    return unless -d $FULLSIZE_IMAGE_DIRECTORY;

    opendir(my $full_dh, $FULLSIZE_IMAGE_DIRECTORY) or return;
    my @full_images = grep {
        -f "$FULLSIZE_IMAGE_DIRECTORY/$_" && /\.(jpg|jpeg|png|gif|bmp|tiff?)$/i
    } readdir($full_dh);
    closedir($full_dh);
    debug_line("Found " . scalar @full_images . " image(s) in fullsize directory.");

    foreach my $file (@full_images) {
        my $full_path = "$FULLSIZE_IMAGE_DIRECTORY/$file";
        my ($basename, $ext) = $file =~ /^(.+)\.([^.]+)$/;
        next unless $basename;

        # Check if any preview variants are missing
        my $missing_previews = 0;

        # Check standard preview (maintains original format for transparency)
        my $has_transparency = ($ext =~ /^(png|gif)$/i);
        my $preview_ext = $has_transparency ? "png" : "jpg";
        my $standard_preview = "$PREVIEW_DIRECTORY/${basename}.${preview_ext}";
        unless (-f $standard_preview) {
            debug_line("Missing standard preview for '${file}'");
            $missing_previews = 1;
        }

        # Check legacy preview (always GIF, check both old and new locations)
        my $legacy_new = "$LEGACY_PREVIEW_STANDARD_DIRECTORY/${basename}.gif";
        my $legacy_old = "$LEGACY_PREVIEW_DIRECTORY/${basename}.gif";
        unless (-f $legacy_new || -f $legacy_old) {
            debug_line("Missing legacy preview for '${file}'");
            $missing_previews = 1;
        }

        # Check collage thumbnail (always GIF)
        my $collage_thumb = "$COLLAGE_THUMBNAIL_DIRECTORY/${basename}.gif";
        unless (-f $collage_thumb) {
            debug_line("Missing collage thumbnail for '${file}'");
            $missing_previews = 1;
        }

        # Regenerate all previews if any are missing
        if ($missing_previews) {
            debug_line("Regenerating previews for '${file}'...");
            generate_image_previews($full_path, $file);
            print "." if ($_INTERACTIVE);  # Progress indicator
            $processed_count++;
        }
    }

    # Finish progress line
    print "\n" if ($_INTERACTIVE && $processed_count > 0);

    # Bulk migration of remaining legacy previews (maintenance mode only)
    # Migrate any stragglers that weren't caught by on-access migration
    if ($_INTERACTIVE && -d $LEGACY_PREVIEW_DIRECTORY) {
        debug_line("Scanning for unmigrated legacy previews...");

        opendir(my $legacy_dh, $LEGACY_PREVIEW_DIRECTORY);
        my @legacy_gifs = grep {
            -f "$LEGACY_PREVIEW_DIRECTORY/$_" && /\.gif$/i
        } readdir($legacy_dh);
        closedir($legacy_dh);

        my $migrated_count = 0;

        if (@legacy_gifs) {
            print "Migrating " . scalar(@legacy_gifs) . " legacy preview(s) to new structure...\n";

            # Ensure target directory exists
            unless (-d $LEGACY_PREVIEW_STANDARD_DIRECTORY) {
                mkdir($LEGACY_PREVIEW_STANDARD_DIRECTORY);
            }

            foreach my $file (@legacy_gifs) {
                my $old_path = "$LEGACY_PREVIEW_DIRECTORY/$file";
                my $new_path = "$LEGACY_PREVIEW_STANDARD_DIRECTORY/$file";

                # Skip if target already exists (newer file wins)
                unless (-f $new_path) {
                    if (rename($old_path, $new_path)) {
                        debug_line("Migrated legacy preview: $file");
                        print ".";
                        $migrated_count++;
                    } else {
                        debug_line("Failed to migrate $file: $!");
                    }
                } else {
                    debug_line("Skipped $file - newer version exists in target");
                    # Remove old file since new one exists
                    unlink($old_path);
                }
            }

            print "\n" if $migrated_count > 0;
            print "Successfully migrated $migrated_count legacy preview(s).\n";
        } else {
            debug_line("No unmigrated legacy previews found.");
        }
    }

    # Clean up orphaned previews
    debug_line("Checking for orphaned previews...");
    cleanup_orphaned_previews();
}

# Generate previews in the local image directory using server-side tools
sub generate_image_previews {
    my ($full_path, $filename) = @_;
    debug_line("Entering subroutine: generate_image_previews('" . $full_path . "','" . $filename . "')");
    
    # Use configured directories with fallbacks
    my $preview_dir = $PREVIEW_DIRECTORY || "${IMAGE_DIRECTORY}/previews";
    my $legacy_dir = $LEGACY_PREVIEW_DIRECTORY || "${preview_dir}/legacy";
    debug_line("Preview directories are '${preview_dir}' and '${legacy_dir}'");
    
    # Use configured widths with fallbacks (targeting display resolutions)
    my $preview_width = $PREVIEW_WIDTH || "1024";
    my $legacy_width = $LEGACY_PREVIEW_WIDTH || "600";
    debug_line("Preview dimensions: x${preview_width} (standard) and x${legacy_width} (legacy)");
    
    # Extract basename and extension
    my ($basename, $ext) = $filename =~ /^(.+)\.([^.]+)$/;
    return unless $basename;
   
    # Create preview directories if they don't exist
    mkdir $preview_dir unless -d $preview_dir;
    mkdir $legacy_dir unless -d $legacy_dir;
    
    # Check for image processing tools
    debug_line("Detecting image processing tools on server...");
    my $has_imagemagick = `which convert 2>/dev/null`;
    my $has_gm = `which gm 2>/dev/null`;
    chomp($has_imagemagick);
    chomp($has_gm);
    debug_line("Server appears to have ImageMagick installed for preview generation.") if ($has_imagemagick);
    debug_line("Server appears to have GraphicsMagick installed for preview generation.") if ($has_gm);

    # Skip if no tools available
    debug_line("Host has no tools installed for preview generation. Returning...") unless ($has_imagemagick || $has_gm);
    return unless ($has_imagemagick || $has_gm);
    
    # Determine if image has transparency
    my $has_transparency = 0;
    if ($has_imagemagick) {
        my $check = `convert '$full_path' -format "%[opaque]" info: 2>/dev/null`;
        chomp($check);
        $has_transparency = ($check eq "False");
    } elsif ($has_gm) {
        # Simple assumption for GM
        $has_transparency = $ext =~ /^(png|gif)$/i;
    }
    
    # Generate standard preview (width-constrained only)
    my $preview_ext = $has_transparency ? "png" : "jpg";
    my $preview_path = "$preview_dir/${basename}.${preview_ext}";
    
    unless (-f $preview_path) {
        if ($has_imagemagick) {
            my $quality = $has_transparency ? "" : "-quality 85";
            # Use width constraint only, height scales proportionally
            system("convert '$full_path' -resize '${preview_width}>' $quality '$preview_path' 2>/dev/null");
        } elsif ($has_gm) {
            my $quality = $has_transparency ? "" : "-quality 85";
            system("gm convert '$full_path' -resize '${preview_width}>' $quality '$preview_path' 2>/dev/null");
        }
    }
    
    # Generate legacy GIF preview (width-constrained for 640x480 displays)
    # Check new semantic location first, fall back to old location
    my $legacy_standard_dir = $LEGACY_PREVIEW_STANDARD_DIRECTORY || $legacy_dir;
    my $legacy_path = "$legacy_standard_dir/${basename}.gif";
    my $old_legacy_path = "$legacy_dir/${basename}.gif";

    # Generate in new location if it doesn't exist anywhere
    unless (-f $legacy_path || -f $old_legacy_path) {
        mkdir $legacy_standard_dir unless -d $legacy_standard_dir;
        if ($has_imagemagick) {
            # Web-safe colors for old displays, width-based sizing
            system("convert '$full_path' -resize '${legacy_width}>' " .
                   "-dither FloydSteinberg -colors 216 " .
                   "'$legacy_path' 2>/dev/null");
        } elsif ($has_gm) {
            system("gm convert '$full_path' -resize '${legacy_width}>' " .
                   "-dither -colors 216 '$legacy_path' 2>/dev/null");
        }
    }

    # Generate collage thumbnails (small GIF for legacy browser collages)
    my $collage_width = $COLLAGE_THUMBNAIL_WIDTH || "300";
    my $collage_dir = $COLLAGE_THUMBNAIL_DIRECTORY || "${legacy_dir}/collage";
    my $collage_path = "$collage_dir/${basename}.gif";
    debug_line("Collage thumbnail dimensions: x${collage_width}");

    unless (-f $collage_path) {
        mkdir $collage_dir unless -d $collage_dir;
        if ($has_imagemagick) {
            # Small GIF optimized for collages on legacy browsers
            system("convert '$full_path' -resize '${collage_width}>' " .
                   "-dither FloydSteinberg -colors 216 " .
                   "'$collage_path' 2>/dev/null");
        } elsif ($has_gm) {
            system("gm convert '$full_path' -resize '${collage_width}>' " .
                   "-dither -colors 216 '$collage_path' 2>/dev/null");
        }
    }
}

# Clean up orphaned preview files
# Scans all preview directories and removes files whose fullsize originals no longer exist
sub cleanup_orphaned_previews {
    debug_line("Entering subroutine: cleanup_orphaned_previews()");

    return unless -d $FULLSIZE_IMAGE_DIRECTORY;

    my @preview_dirs = (
        { path => $PREVIEW_DIRECTORY, type => 'standard', pattern => qr/\.(jpg|jpeg|png|gif)$/i },
        { path => $LEGACY_PREVIEW_STANDARD_DIRECTORY, type => 'legacy standard', pattern => qr/\.gif$/i },
        { path => $LEGACY_PREVIEW_DIRECTORY, type => 'legacy (old location)', pattern => qr/\.gif$/i },
        { path => $COLLAGE_THUMBNAIL_DIRECTORY, type => 'collage thumbnail', pattern => qr/\.gif$/i }
    );

    my $total_removed = 0;
    my $total_size_freed = 0;

    foreach my $dir_info (@preview_dirs) {
        my $preview_dir = $dir_info->{path};
        my $dir_type = $dir_info->{type};
        my $pattern = $dir_info->{pattern};

        next unless -d $preview_dir;

        debug_line("Scanning ${dir_type} preview directory: ${preview_dir}");

        opendir(my $dh, $preview_dir) or next;
        my @previews = grep { -f "$preview_dir/$_" && /$pattern/ } readdir($dh);
        closedir($dh);

        foreach my $preview_file (@previews) {
            # Extract basename (remove extension)
            my ($basename) = $preview_file =~ /^(.+)\.[^.]+$/;
            next unless $basename;

            # Check if corresponding fullsize image exists (any supported format)
            my @fullsize_extensions = ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif');
            my $fullsize_exists = 0;

            foreach my $ext (@fullsize_extensions) {
                if (-f "$FULLSIZE_IMAGE_DIRECTORY/${basename}.${ext}") {
                    $fullsize_exists = 1;
                    last;
                }
            }

            # Remove orphaned preview if fullsize doesn't exist
            unless ($fullsize_exists) {
                my $preview_path = "$preview_dir/$preview_file";
                my $file_size = -s $preview_path || 0;

                if (unlink($preview_path)) {
                    debug_line("Removed orphaned ${dir_type} preview: ${preview_file}");
                    print "Removed orphaned ${dir_type} preview: ${preview_file}\n" if ($_INTERACTIVE);
                    $total_removed++;
                    $total_size_freed += $file_size;
                } else {
                    debug_line("Failed to remove orphaned preview ${preview_file}: $!");
                }
            }
        }
    }

    if ($total_removed > 0 && $_INTERACTIVE) {
        my $size_str = "";
        if ($total_size_freed >= 1048576) {  # 1MB
            $size_str = sprintf(" (%.2f MB freed)", $total_size_freed / 1048576);
        } elsif ($total_size_freed >= 1024) {  # 1KB
            $size_str = sprintf(" (%.2f KB freed)", $total_size_freed / 1024);
        } elsif ($total_size_freed > 0) {
            $size_str = sprintf(" (%d bytes freed)", $total_size_freed);
        }
        print "Cleanup complete: removed ${total_removed} orphaned preview(s)${size_str}\n";
    } elsif ($_INTERACTIVE) {
        debug_line("No orphaned previews found.");
    }

    return $total_removed;
}

# Get random image and return the file path
sub random_image {
  # If recursive mode is enabled in config, use recursive search
  if ($IMAGE_API_RECURSE) {
    return random_image_recursive();
  }

  # Otherwise, search API image directory (both processed and unprocessed)
  return if (! -d $API_IMAGE_DIRECTORY);

  # Extract relative structure from config and apply to API directory
  my $fullsize_subdir = get_relative_subdir($IMAGE_DIRECTORY, $FULLSIZE_IMAGE_DIRECTORY);
  my $api_fullsize_dir = $fullsize_subdir ? "${API_IMAGE_DIRECTORY}/${fullsize_subdir}" : "${API_IMAGE_DIRECTORY}/full";

  # Image file pattern
  my $image_pattern = qr/\.(jpg|jpeg|png|gif|bmp|tiff?)$/i;

  my @images;

  # Priority 1: Collect processed images from full/ subdirectory
  if (-d $api_fullsize_dir) {
    opendir(my $dh, $api_fullsize_dir) or return;
    my @processed = grep { -f "$api_fullsize_dir/$_" && /$image_pattern/ } readdir($dh);
    closedir($dh);
    push @images, map { "$api_fullsize_dir/$_" } @processed;
  }

  # Priority 2: Collect unprocessed images from base directory
  opendir(my $dh, $API_IMAGE_DIRECTORY) or return;
  my @unprocessed = grep { -f "$API_IMAGE_DIRECTORY/$_" && /$image_pattern/ } readdir($dh);
  closedir($dh);
  push @images, map { "$API_IMAGE_DIRECTORY/$_" } @unprocessed;

  # Select random image from combined list
  my $image_count = scalar @images;
  return if (!$image_count);
  my $selection = int(rand($image_count));
  return $images[$selection];
}

# Get random image recursively from directory tree and return the file path
sub random_image_recursive {
  my $dir = shift || cwd();  # Start from current directory if none specified
  return if (!$dir);

  my @all_images;

  # Extract relative structure from config
  my $fullsize_subdir = get_relative_subdir($IMAGE_DIRECTORY, $FULLSIZE_IMAGE_DIRECTORY);
  $fullsize_subdir = "full" unless $fullsize_subdir;

  # Image file pattern
  my $image_pattern = qr/\.(jpg|jpeg|png|gif|bmp|tiff?)$/i;

  # Helper function to recursively find image files
  my $find_images;
  $find_images = sub {
    my $current_dir = shift;
    return if (!$current_dir || ! -d $current_dir);

    opendir(my $dh, $current_dir) or return; # Skip if can't open
    my @entries = grep { !/^\.\.?$/ } readdir($dh);
    closedir($dh);
    foreach my $entry (@entries) {
      my $path = "$current_dir/$entry";
      if (-d $path) {
        # Check if this directory is an API image directory
        if ($entry eq basename($API_IMAGE_DIRECTORY)) {
          # Search both processed and unprocessed locations
          my $fullsize_path = "$path/$fullsize_subdir";

          # Priority 1: Processed images from full/ subdirectory
          if (-d $fullsize_path) {
            opendir(my $pdh, $fullsize_path) or next;
            my @processed = grep { -f "$fullsize_path/$_" && /$image_pattern/ } readdir($pdh);
            closedir($pdh);
            push @all_images, map { "$fullsize_path/$_" } @processed;
          }

          # Priority 2: Unprocessed images from base directory
          opendir(my $pdh, $path) or next;
          my @unprocessed = grep { -f "$path/$_" && /$image_pattern/ } readdir($pdh);
          closedir($pdh);
          push @all_images, map { "$path/$_" } @unprocessed;
        }
        # Recursively search subdirectories
        $find_images->($path);
      }
    }
  };

  # Start the recursive search from the current directory
  $find_images->($dir);

  my $image_count = scalar @all_images;
  return if (!$image_count);

  my $selection = int(rand($image_count));
  return $all_images[$selection];
}

# Transliterate accented characters to ASCII equivalents
# Handles common European accented characters (Nordic, Romance languages, etc.)
sub transliterate_to_ascii {
  my $text = shift;
  return '' unless ($text);

  # Common accented vowels to ASCII
  $text =~ s/[àáâãäåāăą]/a/g;
  $text =~ s/[ÀÁÂÃÄÅĀĂĄ]/A/g;
  $text =~ s/[èéêëēĕėęě]/e/g;
  $text =~ s/[ÈÉÊËĒĔĖĘĚ]/E/g;
  $text =~ s/[ìíîïĩīĭį]/i/g;
  $text =~ s/[ÌÍÎÏĨĪĬĮ]/I/g;
  $text =~ s/[òóôõöøōŏő]/o/g;
  $text =~ s/[ÒÓÔÕÖØŌŎŐ]/O/g;
  $text =~ s/[ùúûüũūŭů]/u/g;
  $text =~ s/[ÙÚÛÜŨŪŬŮ]/U/g;
  $text =~ s/[ýÿ]/y/g;
  $text =~ s/[ÝŸ]/Y/g;

  # Nordic/Icelandic special characters
  $text =~ s/[æ]/ae/g;
  $text =~ s/[Æ]/AE/g;
  $text =~ s/[ð]/d/g;
  $text =~ s/[Ð]/D/g;
  $text =~ s/[þ]/th/g;
  $text =~ s/[Þ]/TH/g;

  # Other common characters
  $text =~ s/[ç]/c/g;
  $text =~ s/[Ç]/C/g;
  $text =~ s/[ñ]/n/g;
  $text =~ s/[Ñ]/N/g;
  $text =~ s/[ß]/ss/g;

  return $text;
}

# Parse .aliases file and return hash of alias => path mappings
# Aliases are normalized (transliterated + lowercased) for matching
sub parse_aliases_file {
  my $aliases_file = shift;
  return unless (-f $aliases_file);

  my %aliases;
  open(my $fh, '<:utf8', $aliases_file) or return;
  while (my $line = <$fh>) {
    chomp $line;
    # Skip comments and empty lines
    next if ($line =~ /^\s*#/ || $line =~ /^\s*$/);
    # Parse alias=path format
    if ($line =~ /^\s*(.+?)\s*=\s*(.+?)\s*$/) {
      my ($alias, $path) = ($1, $2);
      # Normalize: transliterate accents, then lowercase
      my $normalized_alias = lc(transliterate_to_ascii($alias));
      $aliases{$normalized_alias} = $path;
    }
  }
  close($fh);
  return %aliases;
}

# Search for alias in current directory, then immediate subdirectories (two-level search)
# Performs case-insensitive and accent-insensitive matching
sub resolve_alias {
  my $alias_query = shift;
  return unless ($alias_query);

  # Normalize query: transliterate accents, then lowercase
  my $normalized_query = lc(transliterate_to_ascii($alias_query));

  my $current_dir = get_logical_cwd();
  my $aliases_file = "${current_dir}/.aliases";

  # Level 1: Check current directory's .aliases file
  if (-f $aliases_file) {
    my %aliases = parse_aliases_file($aliases_file);
    return $aliases{$normalized_query} if (exists $aliases{$normalized_query});
  }

  # Level 2: Check immediate subdirectories' .aliases files
  return unless (-d $current_dir);
  opendir(my $dh, $current_dir) or return;
  my @subdirs = grep { -d "${current_dir}/$_" && !/^\./ } readdir($dh);
  closedir($dh);

  foreach my $subdir (@subdirs) {
    my $subdir_aliases = "${current_dir}/${subdir}/.aliases";
    next unless (-f $subdir_aliases);

    my %aliases = parse_aliases_file($subdir_aliases);
    if (exists $aliases{$normalized_query}) {
      # Return path relative to current directory (subdir/mapped_path)
      my $mapped_path = $aliases{$normalized_query};
      return "${subdir}/${mapped_path}";
    }
  }

  return; # No alias found
}

# Get random image from a specific subdirectory path
sub random_image_from_path {
  my $subpath = shift;
  return if (!$subpath);

  # Try to resolve alias first (before sanitization to preserve original query)
  my $resolved_path = resolve_alias($subpath);
  $subpath = $resolved_path if ($resolved_path);

  # Sanitize path to prevent directory traversal attacks
  # Remove any ../ patterns, leading/trailing slashes
  $subpath =~ s/\.\.//g;           # Remove all .. patterns
  $subpath =~ s/^\/+//;            # Remove leading slashes
  $subpath =~ s/\/+$//;            # Remove trailing slashes
  $subpath =~ s/\/\/+/\//g;        # Collapse multiple slashes

  return if (!$subpath);           # Return if sanitization left nothing

  # Construct target directory path relative to current script location
  my $current_dir = get_logical_cwd();
  $current_dir =~ s/\/$//;         # Remove trailing slash
  my $target_dir = "${current_dir}/${subpath}";

  # Verify the target directory exists
  return if (! -d $target_dir);

  # Check if resolved path is still within DOCUMENT_ROOT (security check)
  my $resolved_path = abs_path($target_dir) || $target_dir;
  my $doc_root = abs_path($ENV{DOCUMENT_ROOT}) || $ENV{DOCUMENT_ROOT};
  $resolved_path =~ s/\/$//;
  $doc_root =~ s/\/$//;
  return if ($resolved_path !~ /^\Q$doc_root\E/);

  # If recursive mode is enabled in config, recursively search from target directory
  if ($IMAGE_API_RECURSE) {
    return random_image_recursive($target_dir);
  }

  # Otherwise, search target directory's API image directory (both processed and unprocessed)
  # Look for API image directory within the target
  my $image_dir = "${target_dir}/${API_IMAGE_DIRECTORY}";
  return if (! -d $image_dir);

  # Extract relative structure from config and apply to target directory
  my $fullsize_subdir = get_relative_subdir($IMAGE_DIRECTORY, $FULLSIZE_IMAGE_DIRECTORY);
  my $fullsize_dir = $fullsize_subdir ? "${image_dir}/${fullsize_subdir}" : "${image_dir}/full";

  # Image file pattern
  my $image_pattern = qr/\.(jpg|jpeg|png|gif|bmp|tiff?)$/i;

  my @images;

  # Priority 1: Collect processed images from full/ subdirectory
  if (-d $fullsize_dir) {
    opendir(my $dh, $fullsize_dir) or return;
    my @processed = grep { -f "$fullsize_dir/$_" && /$image_pattern/ } readdir($dh);
    closedir($dh);
    push @images, map { "$fullsize_dir/$_" } @processed;
  }

  # Priority 2: Collect unprocessed images from base directory
  opendir(my $dh, $image_dir) or return;
  my @unprocessed = grep { -f "$image_dir/$_" && /$image_pattern/ } readdir($dh);
  closedir($dh);
  push @images, map { "$image_dir/$_" } @unprocessed;

  # Select random image from combined list
  my $image_count = scalar @images;
  return if (!$image_count);

  my $selection = int(rand($image_count));
  return $images[$selection];
}

# URL decode and handle UTF-8 properly
sub url_decode {
  my $str = shift;
  return '' unless defined $str;

  # Replace + with space
  $str =~ s/\+/ /g;

  # Decode %XX sequences
  $str =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/eg;

  # Ensure string is treated as UTF-8
  utf8::decode($str) unless utf8::is_utf8($str);

  return $str;
}

# API handler
sub handle_api_request {
	if ($API_ENABLED) {
  	my $query_string = $ENV{QUERY_STRING} || '';
  	my @pairs = split(/[&;]/, $query_string);
  	foreach(@pairs)
  	{
    	my($key, $value) = split(/=/, $_, 2);

    	# URL decode the value
    	$value = url_decode($value) if defined $value;

    	if ($key eq 'random-image') {
      	my $image_path;
      	my $search_location = $value || "current directory";

      	# Route based on value
      	if ($value && $value ne '') {
        	# Value provided: treat as subdirectory path
        	$image_path = random_image_from_path($value);
      	} else {
        	# No value or empty: current directory
        	# (recursion controlled by $IMAGE_API_RECURSE config)
        	$image_path = random_image();
      	}

      	if ($image_path && -f $image_path) {
        	# Get the file extension to determine content type
        	my $content_type = 'image/jpeg';  # Default to JPEG
        	if ($image_path =~ /\.png$/i) {
          	$content_type = 'image/png';
        	} elsif ($image_path =~ /\.gif$/i) {
          	$content_type = 'image/gif';
        	}

        	# Read and output the image file
        	if (open(my $image, '<', $image_path)) {
          	binmode($image);
          	print "Content-type: ${content_type}\n\n";
          	print do { local $/; <$image> };
          	close($image);
          	return 1;
        	}
      	} else {
        	# API request detected but no image found - return 404 error
        	print "Status: 404 Not Found\n";
        	print "Content-type: text/plain\n\n";
        	print "Error: No images found";
        	print " in location: $search_location" if ($value);
        	print "\n";
        	return 1;
      	}
    	}
  	}
	}
  return 0;
}

# Content generation -------------------------------------------------------- #
my $_NSI_CONTENT;

# Handle arguments when called interactively or from cron 
if (!$_WWW_EXEC) {
  use Getopt::Long;
  
  # Set up command line options
  my $cli_config;
  my $cli_root;
  my $cli_process_images;
  my $cli_target_dir;
  my $cli_help;
  my $cli_verbose;
  
  GetOptions(
    'config=s'         => \$cli_config,
    'root=s'           => \$cli_root,
    'process-images'   => \$cli_process_images,
    'target=s'         => \$cli_target_dir,
    'verbose'          => \$cli_verbose,
    'help'             => \$cli_help
  ) or die "Error in command line arguments. Use --help for usage.\n";
  
  # Enable debug trace if verbose mode requested
  $DEBUG_TRACE = 1 if $cli_verbose;
  
  # Display help if requested
  if ($cli_help) {
    print <<'HELP';
NSI Command Line Interface
--------------------------
Usage: index.cgi [OPTIONS]

Options:
  --config=FILE        Specify configuration file path
  --root=PATH          Set document root (required without CGI environment)
  --process-images     Process images in target directory
  --target=PATH        Target directory for operations (default: current)
  --verbose            Enable debug output
  --help               Show this help message

Examples:
  # Process images in current directory
  ./index.cgi --config=/var/www/res/config.pl --root=/var/www --process-images
  
  # Process images in specific directory
  ./index.cgi --config=/var/www/res/config.pl --root=/var/www --process-images --target=/var/www/gallery
  
  # Run with verbose output for troubleshooting
  ./index.cgi --config=/var/www/res/config.pl --root=/var/www --process-images --verbose
HELP
    exit 0;
  }
  
  # Set document root if provided (Workaround #1: Manual environment setup)
  if ($cli_root) {
    $ENV{DOCUMENT_ROOT} = $cli_root;
    $ENV{DOCUMENT_ROOT} =~ s/\/$//;  # Remove trailing slash for consistency
    debug_line("Document root set to: $ENV{DOCUMENT_ROOT}");
  } elsif (!$ENV{DOCUMENT_ROOT}) {
    # Try to use current directory as fallback if no root specified
    # (Workaround #2: Fallback to pwd when no root provided)
    $ENV{DOCUMENT_ROOT} = cwd();
    debug_line("Warning: No document root specified, using current directory: $ENV{DOCUMENT_ROOT}");
  }
  
  # Override config file path if specified
  if ($cli_config) {
    if (-f $cli_config) {
      $_SITE_CONFIG = $cli_config;
      debug_line("Using specified config file: $_SITE_CONFIG");
    } else {
      die "Error: Specified config file does not exist: $cli_config\n";
    }
  }
  
    # Reload configuration with new paths (Workaround #3: Force config reload)
    # We need to re-process configs since we may have changed paths
    unless ($cli_config) {
      my $search_path = cwd();
      while ($search_path ne '/') {
          my $potential_config = "$search_path/$_SITE_CONFIG_NAME";
          if (-f $potential_config) {
              $_SITE_CONFIG = $potential_config;
              last;
          }
          $search_path = dirname($search_path);
      }
    }
  
    # Process configuration files again with correct paths
    if (-f $_SITE_CONFIG && !do $_SITE_CONFIG) { 
      die "Error loading site configuration: $@\n";
    }
    if (-f $_LOCAL_CONFIG && !do $_LOCAL_CONFIG) {
      warn "Warning: Error loading local configuration: $@\n";
    }  
  # Handle image processing request
  if ($cli_process_images) {
    my $target = $cli_target_dir || cwd();
    
    # Change to target directory for processing
    # (Workaround #4: Temporary directory change for context-dependent operations)
    my $original_dir = cwd();
    chdir($target) or die "Cannot change to target directory: $target\n";
    
    print "Processing images in: $target\n";
    debug_line("Starting image processing in: $target");

    # Set up image directory paths relative to current location
    $IMAGE_DIRECTORY = "./res/img" unless $IMAGE_DIRECTORY;
    $FULLSIZE_IMAGE_DIRECTORY = "${IMAGE_DIRECTORY}/full" unless $FULLSIZE_IMAGE_DIRECTORY;
    $PREVIEW_DIRECTORY = "${IMAGE_DIRECTORY}/previews" unless $PREVIEW_DIRECTORY;
    $LEGACY_PREVIEW_DIRECTORY = "${PREVIEW_DIRECTORY}/legacy" unless $LEGACY_PREVIEW_DIRECTORY;

    # Count images to be processed
    my $total_to_process = 0;
    my $loose_count = 0;
    my $missing_preview_count = 0;
    my $total_size = 0;

    # Count loose files in base directory
    if (-d $IMAGE_DIRECTORY) {
        opendir(my $dh, $IMAGE_DIRECTORY);
        my @loose = grep { -f "$IMAGE_DIRECTORY/$_" && /\.(jpg|jpeg|png|gif|bmp|tiff?)$/i } readdir($dh);
        closedir($dh);
        $loose_count = scalar @loose;

        # Track file sizes
        foreach my $file (@loose) {
            $total_size += -s "$IMAGE_DIRECTORY/$file" || 0;
        }
    }

    # Count images in fullsize directory needing preview regeneration
    if (-d $FULLSIZE_IMAGE_DIRECTORY) {
        opendir(my $dh, $FULLSIZE_IMAGE_DIRECTORY);
        my @full_images = grep { -f "$FULLSIZE_IMAGE_DIRECTORY/$_" && /\.(jpg|jpeg|png|gif|bmp|tiff?)$/i } readdir($dh);
        closedir($dh);

        foreach my $file (@full_images) {
            my ($basename, $ext) = $file =~ /^(.+)\.([^.]+)$/;
            next unless $basename;

            # Check if any previews are missing
            my $has_transparency = ($ext =~ /^(png|gif)$/i);
            my $preview_ext = $has_transparency ? "png" : "jpg";
            my $standard_preview = "$PREVIEW_DIRECTORY/${basename}.${preview_ext}";
            my $legacy_new = "$LEGACY_PREVIEW_STANDARD_DIRECTORY/${basename}.gif";
            my $legacy_old = "$LEGACY_PREVIEW_DIRECTORY/${basename}.gif";
            my $collage_thumb = "$COLLAGE_THUMBNAIL_DIRECTORY/${basename}.gif";

            unless ((-f $standard_preview) && ((-f $legacy_new) || (-f $legacy_old)) && (-f $collage_thumb)) {
                $missing_preview_count++;
                # Track file size
                $total_size += -s "$FULLSIZE_IMAGE_DIRECTORY/$file" || 0;
            }
        }
    }

    $total_to_process = $loose_count + $missing_preview_count;

    if ($total_to_process > 0) {
        # Format file size
        my $size_str = "";
        my $avg_str = "";
        if ($total_size > 0) {
            if ($total_size >= 1073741824) {  # 1GB
                $size_str = sprintf("%.2f GB", $total_size / 1073741824);
            } elsif ($total_size >= 1048576) {  # 1MB
                $size_str = sprintf("%.2f MB", $total_size / 1048576);
            } elsif ($total_size >= 1024) {  # 1KB
                $size_str = sprintf("%.2f KB", $total_size / 1024);
            } else {
                $size_str = sprintf("%d bytes", $total_size);
            }

            my $avg_size = $total_size / $total_to_process;
            if ($avg_size >= 1048576) {  # 1MB
                $avg_str = sprintf("%.2f MB", $avg_size / 1048576);
            } elsif ($avg_size >= 1024) {  # 1KB
                $avg_str = sprintf("%.2f KB", $avg_size / 1024);
            } else {
                $avg_str = sprintf("%d bytes", $avg_size);
            }
        }

        print "Found $total_to_process image(s) to process";
        print " ($size_str total, $avg_str average)" if $size_str;
        print ":\n";
        print "  - $loose_count loose file(s) to move and process\n" if $loose_count > 0;
        print "  - $missing_preview_count image(s) with missing previews\n" if $missing_preview_count > 0;
    } else {
        print "No images require processing.\n";
    }

    # Call the image processing function
    process_page_images();
    
    # Return to original directory
    chdir($original_dir);
    
    print "Image processing complete.\n";
    debug_line("Image processing completed");
  }
  
  # Exit after CLI operations (don't generate HTML output)
  exit 0;
}

# Check for API requests first
if (handle_api_request()) {
  exit;
}


# Content generation: body.html, body/ fragments, or dynamic
my $has_body_file = -f $BODY_FILE;
my $has_body_dir = -d "body";

if ($has_body_file || $has_body_dir) {
	# Process body.html if it exists
	if ($has_body_file) {
		if (get_body_file_title) {
			$_NSI_CONTENT .= auto_hr() . strip_body_file_title();
		} else {
			open(my $body_html, '<', $BODY_FILE)
				or die "Cannot open static content file $BODY_FILE";
			{
				local $/;
				$_NSI_CONTENT = auto_hr() . <$body_html>;
			}
			close(body_html);
		}
	}
	# Process body/ fragments if directory exists (appends after body.html)
	if ($has_body_dir) {
		my $fragments = process_body_fragments();
		if ($fragments) {
			# Add HR if fragments-only (no body.html preceded it)
			$_NSI_CONTENT .= auto_hr() if (!$has_body_file);
			$_NSI_CONTENT .= $fragments;
		}
	}
	# Append TOC after body content if enabled
	if ($APPEND_TOC_TO_BODY) {
		$_NSI_CONTENT .= page_toc();
	}
} else {
# Generate a regular dynamic page
	$_NSI_CONTENT .= page_intro();
	$_NSI_CONTENT .= page_toc();
}

# Transform custom NSI image tags
$_NSI_CONTENT = transform_nsi_image_tags($_NSI_CONTENT) if ($_NSI_CONTENT);

# Transform NSI collage blocks (must run after transform_nsi_image_tags)
$_NSI_CONTENT = transform_nsi_collage_tags($_NSI_CONTENT) if ($_NSI_CONTENT);

# Transform NSI banner tags
$_NSI_CONTENT = transform_nsi_banner_tags($_NSI_CONTENT) if ($_NSI_CONTENT);

# Process image previews, if applicable
process_page_images(); 

# Add header and footer

if (!$_NSI_CONTENT) {
	$_NSI_CONTENT = "<I>This page intentionally left blank</I>";
	$_NSI_CONTENT = "<CENTER>${_NSI_CONTENT}</CENTER>\n";
} else {
  $_NSI_PREFORMAT  = page_title();
  $_NSI_PREFORMAT .= navigation_menu() if ($NAV_POSITION > 0);
  $_NSI_PREFORMAT .= $_NSI_CONTENT; 
  $_NSI_PREFORMAT .= navigation_menu() if ($NAV_POSITION < 0); 
  $_NSI_PREFORMAT .= page_footer();
	$_NSI_CONTENT    = $_NSI_PREFORMAT; 
}

$_NSI_CONTENT = "<!-- BEGIN CONTENT -->\n" . $_NSI_CONTENT;
$_NSI_CONTENT .= preformat_text($_DEBUG_TRACE_LINES);
$_NSI_CONTENT .= "<!-- END OF CONTENT -->\n";

$_NSI_PAGE     = "Content-type: text/html\n\n";
$_NSI_PAGE    .= "<!DOCTYPE ${HTML_DOCTYPE}>\n";
$_NSI_PAGE    .= "<!-- Page generated by NSI ${version} -->\n";
$_NSI_PAGE    .= "<HTML>\n";
$_NSI_PAGE    .= "<HEAD>\n";
$_NSI_PAGE    .= generate_metadata();
$_NSI_PAGE    .= "</HEAD>\n";
$_NSI_PAGE    .= "<BODY>\n";
$_NSI_PAGE    .= "<DIV ID=\"content\">\n$_NSI_CONTENT\n</DIV>\n";
$_NSI_PAGE    .= "</BODY>\n";
$_NSI_PAGE    .= "</HTML>\n";

# Content presentation ------------------------------------------------------ #
print $_NSI_PAGE if ($_NSI_CONTENT);
