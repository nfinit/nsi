#!/usr/bin/perl
# NSI: The New Standard Index for simple websites --------------------------- # 
my $version = '2.2.8';
# --------------------------------------------------------------------------- #

$_SITE_ROOT     = $ENV{DOCUMENT_ROOT} . "/";
$_SITE_CONFIG  = $_SITE_ROOT . "res/config.pl";
$_LOCAL_CONFIG = "./.config.pl";

# DO NOT EDIT ANYTHING BELOW THIS LINE
# =========================================================================== #
use Cwd;
use File::Basename;
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

$MEDITATION_DIRECTORY $MEDITATION_FILETYPES

$MAIN_STYLESHEET $LEGACY_STYLESHEET

$SYSTEM_STATUS $STATUS_COMMAND

$HOSTNAME $ORGANIZATION $SITE_NAME
 
);
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
  # print STDERR "Tree TOC requested.\n";
	my @TOC;
	my $target_directory = shift; # Get first argument
	$target_directory = '.' if !$target_directory;
  #print STDERR "Current directory: " . cwd() . "\n";
  # print STDERR "Root directory: " . $ENV{DOCUMENT_ROOT} . "\n";
  # print STDERR "Target directory: ${target_directory}\n";
	if (opendir(ROOT,"${target_directory}")) {
		my @contents = grep !/^.\.*$/, readdir(ROOT);
		closedir(ROOT);
    # print STDERR "Items found: @contents\n";
		foreach $item (@contents) {
        $item = $target_directory . '/' . $item;
			if (-d $item) {
        # print STDERR "Directory: $item\n";
				my $item_data = "${item}/${TOC_FILE}";
        # print STDERR "Searching for ${item_data}...\n";
				if (-f $item_data) {
          # print STDERR "${TOC_FILE} located.\n";
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

# Content generation -------------------------------------------------------- #
my $_NSI_CONTENT;

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
