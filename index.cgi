#!/usr/bin/perl
# NSI: The New Standard Index for simple websites --------------------------- #
my $version = '2.12.0';
# --------------------------------------------------------------------------- #

$_SITE_CONFIG_NAME = "res/config.pl";
$_LOCAL_CONFIG = "./.config.pl";

# DO NOT EDIT ANYTHING BELOW THIS LINE
# =========================================================================== #
use utf8;
use Cwd qw(cwd abs_path);
use File::Basename;
use Time::HiRes qw(time);
# --------------------------------------------------------------------------- #
# All variables can be sourced from either configuration file, however:
# Variables after $SITE_VARS should be sourced from your SITE configuration
# Variables after $LOCAL_VARS should be sourced from your LOCAL configuration 
# --------------------------------------------------------------------------- #
use vars qw(

$LOCAL_VARS

$MEDITATE

$PAGE_TITLE $PAGE_INTRO

$SITE_VARS

$DYNAMIC_LANDING

$HTML_DOCTYPE $CLOUDFLARE

$NAVIGATION_MENU $ROOT_NAVIGATION $TOC_NAV $ROOT_TOC_NAV $NAV_POSITION $FOOTER_NAV $FOOTER_TOP_LINK

$CENTER_TITLE $AUTO_RULE $SUB_LOGO $TREE_TOC $LIST_UL $WRAP_SCRIPT_OUTPUT

$CENTER_IMAGE_CAPTIONS

$SHOW_TOC $TOC_TITLE $TOC_SUBTITLE $APPEND_TOC_TO_BODY

$BODY_FILE $TITLE_FILE $INTRO_FILE $TOC_FILE $GROUP_FILE

$LOGO $FAVICON

$IMAGE_DIRECTORY $API_IMAGE_DIRECTORY $PREVIEW_DIRECTORY
$LEGACY_PREVIEW_DIRECTORY $FULLSIZE_IMAGE_DIRECTORY

$PREVIEW_WIDTH $LEGACY_PREVIEW_WIDTH

$IMAGE_API_RECURSE

$MEDITATION_DIRECTORY $MEDITATION_FILETYPES

$MAIN_STYLESHEET $LEGACY_STYLESHEET

$SYSTEM_STATUS $STATUS_COMMAND

$HOSTNAME $ORGANIZATION $SITE_NAME

$DEBUG_TRACE

);
# Set run mode -------------------------------------------------------------- #
my $_WWW_EXEC;
my $_INTERACTIVE;
$_WWW_EXEC = 1 if ($ENV{GATEWAY_INTERFACE} || $ENV{REQUEST_METHOD});
$_INTERACTIVE = 1 if (!$_WWW_EXEC) and (-t STDERR);
# Configuration processing -------------------------------------------------- #
my $search_path = cwd();
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

# Preprocessing block ------------------------------------------------------- #

chomp $HOSTNAME;
$MEDITATION_FILETYPES =~ s/\./\\\./g;
$MEDITATION_FILETYPES =~ s/\|/\$\|/g;
$MEDITATION_FILETYPES = "${MEDITATION_FILETYPES}\$";


# Utility subroutines ------------------------------------------------------- #

# Use to mark sensitive data blocks 
# (i.e. for hiding from bad actors using Cloudflare)
sub secure_data {
	my $html = shift @_;
	return "<!--sse-->\n${html}<!--/sse-->\n" if ($CLOUDFLARE);
	return $html;
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
  my @meditations = grep /$MEDITATION_FILETYPES/, readdir(MEDITATIONS);
  closedir(MEDITATIONS);
  my $meditation_count = scalar @meditations;
  return if (!$meditation_count);
  my $selection = int(rand($meditation_count));
  $meditation = "$MEDITATION_DIRECTORY/$meditations[$selection]";
  $meditation = "<IMG SRC=\"${meditation}\" CLASS=\"meditation\">\n";
  return($meditation);
}

sub get_body_file_title {
	return if (! -f $BODY_FILE);
	open (my $body_data,"<",$BODY_FILE) or die $!;
	my @body_lines = <$body_data>;
	my @title_lines = grep(/<h1 id="title">/, @body_lines);
	my $title = @title_lines[0];
 	$title =~ s|<.+?>||g;
	return($title);	
}

sub strip_body_file_title {
	return if (! -f $BODY_FILE);
	open (my $body_data,"<",$BODY_FILE) or die $!;
	my @body_full = <$body_data>;
	my @body_lines = grep(!/<h1 id="title">/, @body_full);
	return(join("\n",@body_lines));
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

		# Check if fragment is executable (script)
		if (-x $fragment_path) {
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

		# Look for the image file in the full-size directory
		my @extensions = ('jpg', 'jpeg', 'png', 'gif');
		my $found_file = "";
		my $found_ext = "";

		foreach my $ext (@extensions) {
			my $test_file = "${FULLSIZE_IMAGE_DIRECTORY}/${basename}.${ext}";
			if (-f $test_file) {
				$found_file = $test_file;
				$found_ext = $ext;
				last;
			}
		}

		if ($found_file) {
			# Build the replacement HTML
			my $full_path = "${FULLSIZE_IMAGE_DIRECTORY}/${basename}.${found_ext}";
			my $preview_path = "${PREVIEW_DIRECTORY}/${basename}.${found_ext}";

			$replacement = "<DIV CLASS=\"nsi-image\">\n";
			$replacement .= "  <A HREF=\"${full_path}\">\n";
			$replacement .= "    <IMG SRC=\"${preview_path}\" ALT=\"${alt_text}\">\n";
			$replacement .= "  </A>\n";

			# Add caption if provided
			if ($caption) {
				if ($CENTER_IMAGE_CAPTIONS) {
					$replacement .= "  <CENTER><P CLASS=\"nsi-caption\">${caption}</P></CENTER>\n";
				} else {
					$replacement .= "  <P CLASS=\"nsi-caption\">${caption}</P>\n";
				}
			}

			$replacement .= "</DIV>\n";
		} else {
			# Image not found - leave original tag or show error
			$replacement = "<!-- NSI: Image '${basename}' not found in ${FULLSIZE_IMAGE_DIRECTORY} -->\n";
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

sub get_parent_title {
	# For web requests, use SCRIPT_NAME to get logical parent path
	# (preserves symlink semantics by using URL path instead of filesystem)
	my $parent_dir;

	if ($ENV{SCRIPT_NAME}) {
		# Extract directory from script path (e.g., /galleries/travel/index.cgi -> /galleries/travel)
		my $script_dir = $ENV{SCRIPT_NAME};
		$script_dir =~ s/\/[^\/]+$//;  # Remove /index.cgi

		# Get parent directory from URL path
		if ($script_dir =~ m|^(.*)/[^/]+$|) {
			my $parent_url_path = $1;
			$parent_url_path = "/" if (!$parent_url_path);  # Handle root case

			# Construct absolute filesystem path to parent
			$parent_dir = $ENV{DOCUMENT_ROOT} . $parent_url_path;
		}
	}

	# Fallback to relative path for non-web contexts
	if (!$parent_dir) {
		$parent_dir = "..";
	}

	# Try reading .title file from parent
	my $parent_title_file = "${parent_dir}/${TITLE_FILE}";
	if (-f $parent_title_file) {
		if (open(my $fh, '<', $parent_title_file)) {
			my $title = <$fh>;
			close($fh);
			chomp($title) if ($title);
			return $title if ($title);
		}
	}

	# Try reading .info file from parent (line 1)
	my $parent_info_file = "${parent_dir}/${TOC_FILE}";
	if (-f $parent_info_file) {
		if (open(my $fh, '<', $parent_info_file)) {
			my $title = <$fh>;
			close($fh);
			chomp($title) if ($title);
			return $title if ($title);
		}
	}

	# Fallback to ".."
	return "..";
}

sub get_page_title {
  my $title = "";
  if ($BODY_FILE) {
	  $body_title = get_body_file_title();	
  }
  if ($PAGE_TITLE) 
  { 
    $title = "${PAGE_TITLE}"; 
  } elsif ( -f "${TITLE_FILE}" ) {
    open(my $title_html, '<', $TITLE_FILE)
      or die "Cannot open static content file $TITLE_FILE";
    { 
      local $/;
      $title = <$title_html>;
    }
    close(title_html);
  } elsif ($body_title) {
    $title = $body_title;
  } elsif ($SITE_NAME) {
    $title = $SITE_NAME;
  } elsif (cwd() eq $ENV{DOCUMENT_ROOT}) {
    $title .= "${HOSTNAME}"     if ($HOSTNAME);
    $title .= " @ "             if ($HOSTNAME && $ORGANIZATION);
    $title .= "${ORGANIZATION}" if ($ORGANIZATION);
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
  if ($PAGE_INTRO) 
  { 
    $intro .= "${PAGE_INTRO}"; 
  } elsif ( -f $INTRO_FILE ) {
    open(my $intro_html, '<', $INTRO_FILE)
      or die "Cannot open static content file $INTRO_FILE";
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
sub tree_toc {
	my @TOC;
	my $target_directory = shift; # Get first argument
	$target_directory = '.' if !$target_directory;
	if (opendir(ROOT,"${target_directory}")) {
		my @contents = grep !/^.\.*$/, readdir(ROOT);
		closedir(ROOT);
		foreach $item (@contents) {
        $item = $target_directory . '/' . $item;
			if (-d $item) {
				my $item_data = "${item}/${TOC_FILE}";
				if (-f $item_data) {
					my @item_array;
					my $item_title;
					my $item_path = "${item}/";
          $item_path =~ s/^$ENV{DOCUMENT_ROOT}//;
					my $item_description;
					my $item_group_id;
					my $item_group_display_title;
					my $item_group_description;
					if (open(ITEM_DATA,$item_data)) {
						my $data_line = 0;
						while (<ITEM_DATA>) {
							$item_title = "$_" if (!$data_line);
							$item_description .= "$_" if ($data_line);
							$data_line++;
						}
						close(ITEM_DATA);
					}
					# Read group file if it exists
					# Format: Line 1=group_id, Line 2=display_title, Line 3+=description
					my $item_group = "${item}/${GROUP_FILE}";
					if (-f $item_group) {
						if (open(ITEM_GROUP,$item_group)) {
							my $group_line = 0;
							while (<ITEM_GROUP>) {
								chomp;
								$item_group_id = "$_" if ($group_line == 0);
								$item_group_display_title = "$_" if ($group_line == 1);
								$item_group_description .= "$_" if ($group_line > 1);
								$group_line++;
							}
							close(ITEM_GROUP);
						}
					}
					# Always push all 6 elements to maintain consistent array indices
					# [0]=title, [1]=path, [2]=description, [3]=group_id, [4]=group_display_title, [5]=group_description
					push @item_array, $item_title;
					push @item_array, $item_path;
					push @item_array, $item_description;
					push @item_array, $item_group_id;
					push @item_array, $item_group_display_title;
					push @item_array, $item_group_description;
            				push (@TOC, \@item_array) if ($item_title && $item_path);
				}
			}
		}
	}
	# Sort by group (or title if no group), then by title within group
	@TOC = sort {
		my $group_a = $a->[3] || $a->[0];
		my $group_b = $b->[3] || $b->[0];
		$group_a cmp $group_b || $a->[0] cmp $b->[0]
	} @TOC;
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
	my $contents;
	my $prev_group_id = '';
	my $in_group = 0;
	foreach my $toc_link (@TOC) {
		my $list_item;
    		my $item_name             = @$toc_link[0];
    		my $item_path             = @$toc_link[1];
    		my $item_description      = @$toc_link[2];
    		my $item_group_id         = @$toc_link[3];
    		my $item_group_title      = @$toc_link[4];
    		my $item_group_description = @$toc_link[5];
    		next if (!$item_name);
    		next if (!$item_path);
    		# Check if we've entered a new group with a display title
    		my $current_group = $item_group_id || '';
    		if ($current_group ne $prev_group_id && $item_group_title) {
    			# Close previous nested group if in one
    			if ($LIST_UL && $in_group) {
    				$contents .= "</UL>\n";
    				$in_group = 0;
    			}
    			# Start new group with header and nested list
    			# NOTE: This places H2 and UL directly inside parent UL without
    			# wrapping in LI, which is technically non-compliant with strict
    			# HTML 4.01 but works reliably in all browsers including legacy
    			# clients and avoids bullets on group titles.
    			if ($LIST_UL) {
    				$contents .= "<H2>${item_group_title}</H2>\n";
    				$contents .= "<P>${item_group_description}</P>\n"
    					if ($item_group_description);
    				$contents .= "<UL>\n";
    				$in_group = 1;
    			} else {
    				$contents .= "<H2>${item_group_title}</H2>\n";
    				$contents .= "<P>${item_group_description}</P>\n"
    					if ($item_group_description);
    			}
    		} elsif ($current_group ne $prev_group_id && $in_group) {
    			# Exiting a group (back to ungrouped items)
    			$contents .= "</UL>\n";
    			$in_group = 0;
    		}
    		$prev_group_id = $current_group;
    		$list_item .= "${item_name}";
    		$list_item  = "<A HREF=\"${item_path}\">${list_item}</A>";
    		$list_item  = "<H3>${list_item}</H3>";
    		$list_item .= "\n<P>${item_description}</P>"
                	if ($item_description);
    		$list_item  = "<LI>\n${list_item}\n</LI>" if ($LIST_UL);
    		$list_item .= "\n";
    		$contents .= $list_item;
  	}
  	# Close final group if needed
  	if ($LIST_UL && $in_group) {
  		$contents .= "</UL>\n";
  	}
	return if (!$contents);
	$contents = "<UL>\n${contents}</UL>\n" if ($LIST_UL);
  	$contents = "<P>\n${TOC_SUBTITLE}</P>\n${contents}"
                 if ($TOC_SUBTITLE);
  	$contents = "<H2>${TOC_TITLE}</H2>\n${contents}"
                 if ($TOC_TITLE);
  	$contents = "<DIV ID=\"contents\">\n${contents}</DIV>\n";

  	$contents = auto_hr() . $contents;
	return ($contents);
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
  return if (!$NAVIGATION_MENU);
	# Normalize paths for comparison (handle trailing slash differences)
	my $current_dir = get_logical_cwd();
	my $doc_root = $ENV{DOCUMENT_ROOT};
	$current_dir =~ s/\/$//;
	$doc_root =~ s/\/$//;
	return if (!$ROOT_NAVIGATION && $current_dir eq $doc_root);
  my $menu;
  my @menu_items;
  if ($TOC_NAV) {
    my @TOC;
    my $toc_target;
    if ($ROOT_TOC_NAV) {
      $toc_target = $ENV{DOCUMENT_ROOT};
      $toc_target =~ /\/$/;
    } else {
      $toc_target = get_logical_cwd();
      # Don't traverse above DOCUMENT_ROOT - prevents picking up
      # sibling sites/directories outside the web root
      # Strip trailing slashes for comparison
      my $normalized_target = $toc_target;
      my $normalized_root = $ENV{DOCUMENT_ROOT};
      $normalized_target =~ s/\/$//;
      $normalized_root =~ s/\/$//;
      if ($normalized_target eq $normalized_root) {
        # At root, use current directory (shows children, not siblings)
        # $toc_target already set to current directory above
      } else {
        $toc_target = dirname($toc_target);
      }
    }
    @TOC = toc($toc_target);
    return if (!@TOC);
    my @nav_items = (['Home','/']);
	  push(@nav_items,@TOC);
    my $item_count = 0;
    foreach my $toc_link (@nav_items) {
      my $list_item;
      my $item_name = @$toc_link[0];
      my $item_path = @$toc_link[1];
      next if (!$item_name);
      next if (!$item_path);
      $item_count++;
      $list_item .= "${item_name}";
      if ("$ENV{DOCUMENT_ROOT}${item_path}" eq get_logical_cwd() . '/') {
        $list_item = "<I>${list_item}</I>";
      } elsif (cwd_nested_in($item_path) && ($item_path ne '/')) {
        #$list_item = "<I>${list_item}</I>";
        $list_item = "<B><A HREF=\"${item_path}\">${list_item}</A></B>";
      } else {
        $list_item = "<A HREF=\"${item_path}\">${list_item}</A>";
      }
		  $list_item = $LINE_ELEMENT_DIVIDER . $list_item
        if ($LINE_ELEMENTS && $item_count > 1);
      $list_item = "<SPAN CLASS=\"navigation_item\">${list_item}</SPAN>\n";
      $menu .= $list_item;
    }
  }
  $menu = auto_hr() . $menu;
  $menu = "<DIV ID=\"navigation\" CLASS=\"no_print\">\n${menu}</DIV>\n";
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
		if ($FOOTER_TOP_LINK) {
			$nav_controls .= "<A HREF=\"#content\">Back to top</A>\n";
			# Add divider after if there will be more controls
			if ((!$at_root && !$parent_is_root) || ($NAVIGATION_MENU && $NAV_POSITION >= 0 && !$at_root)) {
				$nav_controls .= $LINE_ELEMENT_DIVIDER if ($LINE_ELEMENTS);
			}
		}

		# Only show parent link if not at root and parent is not the root
		if (!$at_root && !$parent_is_root) {
			my $parent_title = get_parent_title();
			$nav_controls .= "<A HREF=\"..\">${parent_title}</A>\n";
			# Add divider before Home link if needed
			if ($NAVIGATION_MENU && $NAV_POSITION >= 0) {
				$nav_controls .= $LINE_ELEMENT_DIVIDER if ($LINE_ELEMENTS);
			}
		}

		# Show Home link if navigation menu is enabled and not already at root
		if ($NAVIGATION_MENU && $NAV_POSITION >= 0 && !$at_root) {
			$nav_controls .= "<A HREF=\"/\">Home</A>\n";
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

# Landing page dynamic content subroutines ---------------------------------- #

sub status_report {
    	debug_line("Entering subroutine: status_report()");
	return if (!$SYSTEM_STATUS);
	my $command_output;
	my $report = auto_hr . "<H2>Live system status</H2>\n";
	if ($STATUS_COMMAND) {
		$command_output = preformat_text($STATUS_COMMAND);
	} else {
		$command_output = preformat_text(`uptime`);
	}
	return if (!$command_output);
	$report .= "${command_output}\n";
	$report = "<DIV ID=\"status\">\n${report}</DIV>\n";
	$report = secure_data($report);
	return($report); 
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
  $title = '' if ($SITE_NAME eq $title);
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
    my @subdirs = ($FULLSIZE_IMAGE_DIRECTORY, $PREVIEW_DIRECTORY, $LEGACY_PREVIEW_DIRECTORY);
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
   

    foreach my $file (@loose_files) {
	debug_line("Moving lose file '${file}' to '${FULLSIZE_IMAGE_DIRECTORY}' for processing...");	
        my $source = "$img_dir/$file";
        my $dest = "$FULLSIZE_IMAGE_DIRECTORY/$file";
        
        # Move to fullsize directory if not already there
        if (rename($source, $dest)) {
            generate_image_previews($dest, $file);
        }
    }
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
    my $legacy_path = "$legacy_dir/${basename}.gif";
    
    unless (-f $legacy_path) {
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
}

# Get random image and return the file path
sub random_image {
  # If recursive mode is enabled in config, use recursive search
  if ($IMAGE_API_RECURSE) {
    return random_image_recursive();
  }

  # Otherwise, only search current directory's API image directory
  return if (! -d $API_IMAGE_DIRECTORY);
  opendir(IMAGES,$API_IMAGE_DIRECTORY) or die $!;
  my @images = grep /$IMAGE_FILETYPES/, readdir(IMAGES);
  closedir(IMAGES);
  my $image_count = scalar @images;
  return if (!$image_count);
  my $selection = int(rand($image_count));
  return "$API_IMAGE_DIRECTORY/$images[$selection]";
}

# Get random image recursively from directory tree and return the file path
sub random_image_recursive {
  my $dir = shift || cwd();  # Start from current directory if none specified
  return if (!$dir);

  my @all_images;

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
          opendir(my $pdh, $path) or next;
          my @images = grep { /$IMAGE_FILETYPES/ } readdir($pdh);
          closedir($pdh);
          push @all_images, map { "$path/$_" } @images;
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

  # Otherwise, only search the target directory's API image directory
  # Look for API image directory within the target
  my $image_dir = "${target_dir}/${API_IMAGE_DIRECTORY}";
  return if (! -d $image_dir);

  # Get images from this directory
  opendir(my $dh, $image_dir) or return;
  my @images = grep { /$IMAGE_FILETYPES/ } readdir($dh);
  closedir($dh);

  my $image_count = scalar @images;
  return if (!$image_count);

  my $selection = int(rand($image_count));
  return "${image_dir}/$images[$selection]";
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
		$_NSI_CONTENT .= $fragments if ($fragments);
	}
	# Append TOC after body content if enabled
	if ($APPEND_TOC_TO_BODY) {
		$_NSI_CONTENT .= page_toc();
	}
} elsif (cwd() eq $ENV{DOCUMENT_ROOT} && $DYNAMIC_LANDING) {
# If no body file or fragments exist and we are in the root directory,
# generate a dynamic system landing page.
	$_NSI_CONTENT .= page_intro();
	$_NSI_CONTENT .= page_toc();
	$_NSI_CONTENT .= status_report();
} else {
# Generate a regular dynamic page
	$_NSI_CONTENT .= page_intro();
	$_NSI_CONTENT .= page_toc();
}

# Transform custom NSI image tags
$_NSI_CONTENT = transform_nsi_image_tags($_NSI_CONTENT) if ($_NSI_CONTENT);

# Transform NSI collage blocks (must run after transform_nsi_image_tags)
$_NSI_CONTENT = transform_nsi_collage_tags($_NSI_CONTENT) if ($_NSI_CONTENT);

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
