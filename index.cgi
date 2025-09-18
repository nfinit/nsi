#!/usr/bin/perl
# NSI: The New Standard Index for simple websites --------------------------- # 
my $version = '2.6.0';
# --------------------------------------------------------------------------- #

$_SITE_ROOT     = $ENV{DOCUMENT_ROOT} . "/";
$_SITE_CONFIG  = $_SITE_ROOT . "res/config.pl";
$_LOCAL_CONFIG = "./.config.pl";

# DO NOT EDIT ANYTHING BELOW THIS LINE
# =========================================================================== #
use Cwd;
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

$NAVIGATION_MENU $ROOT_NAVIGATION $TOC_NAV $ROOT_TOC_NAV $NAV_POSITION

$CENTER_TITLE $AUTO_RULE $SUB_LOGO $TREE_TOC

$BODY_FILE $TITLE_FILE $INTRO_FILE $TOC_FILE

$LOGO $FAVICON

$IMAGE_DIRECTORY $API_IMAGE_DIRECTORY $PREVIEW_DIRECTORY 
$LEGACY_PREVIEW_DIRECTORY $FULLSIZE_IMAGE_DIRECTORY

$PREVIEW_WIDTH $LEGACY_PREVIEW_WIDTH

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
$DEBUG_TRACE=1 if ($_INTERACTIVE);
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
  $title = "<H1><STRONG>${title}</STRONG></H1>" if ($title);
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
					if (open(ITEM_DATA,$item_data)) {
						my $data_line = 0;
						while (<ITEM_DATA>) {
							$item_title = "$_" if (!$data_line);
							$item_description .= "$_" if ($data_line);
							$data_line++;
						}
						push @item_array, $item_title if ($item_title);
						push @item_array, $item_path if ($item_path);
						push @item_array, $item_description if ($item_description);
            					push (@TOC, \@item_array);
					}
				}
			}
		}
	}
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
	foreach my $toc_link (@TOC) {
		my $list_item;
    		my $item_name        = @$toc_link[0];
    		my $item_path        = @$toc_link[1];
    		my $item_description = @$toc_link[2];
    		next if (!$item_name);
    		next if (!$item_path);
    		$list_item .= "${item_name}";
    		$list_item  = "<A HREF=\"${item_path}\">${list_item}</A>";
    		$list_item  = "<H3>${list_item}</H3>";
    		$list_item .= "\n<P>${item_description}</P>"
                	if ($item_description);
    		$list_item  = "<LI>\n${list_item}\n</LI>" if ($LIST_UL);
    		$list_item .= "\n";
    		$contents .= $list_item;
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
  my $current_directory = cwd();
  $current_directory =~ /\/$/;
  $current_directory =~ s/^$ENV{DOCUMENT_ROOT}//;
  $target_directory  =~ s/^$ENV{DOCUMENT_ROOT}//;
  return $current_directory =~ /^$target_directory/;
}

sub navigation_menu {
  return if (!$NAVIGATION_MENU);
	return if (!$ROOT_NAVIGATION && cwd() eq $ENV{DOCUMENT_ROOT});
  my $menu;
  my @menu_items;
  if ($TOC_NAV) {
    my @TOC;
    my $toc_target;
    if ($ROOT_TOC_NAV) {
      $toc_target = $ENV{DOCUMENT_ROOT};
      $toc_target =~ /\/$/;
    } else {
      $toc_target = cwd();
      $toc_target =~ /\/$/;
      $toc_target = dirname($toc_target);
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
      if ("$ENV{DOCUMENT_ROOT}${item_path}" eq cwd() . '/') {
        $list_item = "<EM>${list_item}</EM>";
      } elsif (cwd_nested_in($item_path) && ($item_path ne '/')) {
        #$list_item = "<EM>${list_item}</EM>";
        $list_item = "<STRONG><A HREF=\"${item_path}\">${list_item}</A></STRONG>";
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
	if ($FOOTER_NAV && cwd() ne $ENV{DOCUMENT_ROOT}) {
		my $footer_nav;
		$footer_nav .= "<SPAN CLASS=\"footer_navigation no_print\">\n";
		$footer_nav .= $LINE_FRAME_L if ($LINE_ELEMENTS);
		$footer_nav .= "<A HREF=\"..\">Up</A>\n";
    if ($NAVIGATION_MENU && $NAV_POSITION >= 0) {
		  $footer_nav .= $LINE_ELEMENT_DIVIDER if ($LINE_ELEMENTS);
		  $footer_nav .= "<A HREF=\"/\">Home</A>\n";
    }
		$footer_nav .= $LINE_FRAME_R if ($LINE_ELEMENTS);
		$footer_nav .= "</SPAN>\n";
		$footer_right .= $footer_nav;
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

# API handler
sub handle_api_request {
	if ($API_ENABLED) {
  	my $query_string = $ENV{QUERY_STRING} || ''; 
  	my @pairs = split(/[&;]/, $query_string);
  	foreach(@pairs)
  	{
    	my($key, $value) = split(/=/, $_, 2);
    	if ($key eq 'random-image') {
      	my $image_path;
      	if ($value eq 'recursive') {
        	$image_path = random_image_recursive();
      	} else {
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
  
}

# Check for API requests first
if (handle_api_request()) {
  exit;
}


# If HTML body file exists, override all content
if (-f $BODY_FILE) {
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
} elsif (cwd() eq $ENV{DOCUMENT_ROOT} && $DYNAMIC_LANDING) { 
# If no body file exists and we are in the root directory,
# generate a dynamic system landing page. 
	$_NSI_CONTENT .= page_intro();
	$_NSI_CONTENT .= page_toc();
	$_NSI_CONTENT .= status_report();
} else {
# Generate a regular dynamic page
	$_NSI_CONTENT .= page_intro();
	$_NSI_CONTENT .= page_toc();
}

# Process image previews, if applicable
process_page_images(); 

# Add header and footer

if (!$_NSI_CONTENT) {
	$_NSI_CONTENT = "<EM>This page intentionally left blank</EM>";
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
