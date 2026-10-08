#!/usr/bin/env perl
###############################################################################
# NSI: The New Standard Index       #                                         #
my $version = '4.0.0.3';            #  A composer engine for simple websites  #
my $author  = 'ict@nfinit.systems'; #                                         #
###############################################################################

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
# Avoid editing this file! Direct changes are easily overwritten by updates,  #
# all of these variables are configurable externally                          #
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Site configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

################# FOR NESTED-SITE DEPLOYMENTS:
$SITE_ROOT = 0; # Configure this to 1 to prevent this page and its children
################# from inheriting configuration settings from any NSI parents

# Default special file paths
$SYSTEM_DIR        = "sys";
$CONFIG_FILE       = "${SYSTEM_DIR}/config"; # Primary config file
$INFO_FILE         = "info"; # Page info file for title, TOC and description
$RESOURCE_DIR      = "res"; # icons, styles and other page cosmetics
$FAVICON_FILE      = "${RESOURCE_DIR}/favicon.ico";
$LOGO_FILE         = "${RESOURCE_DIR}/logo"; # NSI detects extension
$MEDITATION_DIR    = "${RESOURCE_DIR}/meditations";
$STYLE_DIR         = "${RESOURCE_DIR}/style"; # Linked CSS stylesheets
$LEGACY_STYLE_DIR  = "${STYLE_DIR}/legacy"; # Direct-injected legacy CSS
$SCRIPT_DIR        = "${RESOURCE_DIR}/scripts"; # Linked client scripts
$LEGACY_SCRIPT_DIR = "${SCRIPT_DIR}/legacy"; # Direct-injected legacy scripts
$IMAGE_DIR         = "img";
$INTRO_FILE        = "intro.html";
$BODY_FILE         = "body.html"; # single-file body, displays before fragments
$BODY_DIR          = "body";     # fragmented body files and executables

# HTML 4.01 transitional DOCTYPE assists newer browsers with legacy syntax
$HTML_DOCTYPE    = "HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\"";

# Static metadata for all NSI pages
$STATIC_METADATA = <<EOF;
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<META NAME="viewport" CONTENT="width=device-width, initial-scale=1.0">
EOF

# Metadata defaults
$DEFAULT_PAGE_TITLE = "Untitled";
$PAGE_TITLE = "";
$ALT_PAGE_TITLE = ""; # Short title for ToC listings and meta
$SITE_TITLE = "";
$ORG_NAME   = ""; # Useful for server landing pages

# Presentation defaults
$AUTO_HR            = 1;
$NAV_POSITION       = "top";
$TOC                = "bottom";
$CENTER_HEADER      = 0;
$WRAP_SCRIPT_OUTPUT = 0;        # Wrap executable fragments output in <PRE> tags
$IMAGE_FILETYPES    = '\.(gif|jpe?g|png)$';

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Universal helpers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# PLAIN TEXT
# Strip tags and escape HTML for use in <TITLE> and attribute values
sub plain_text {
	my ($text) = @_;
	$text =~ s/<[^>]*>//g;                         # drop tags
	$text =~ s/\s+/ /g;                            # one line, single spaces
	$text =~ s/^ //;
	$text =~ s/ $//;
	$text =~ s/&(?![A-Za-z]+;|#[0-9]+;)/&amp;/g;   # bare & only, keep &amp; etc.
	$text =~ s/</&lt;/g;
	$text =~ s/>/&gt;/g;
	$text =~ s/"/&quot;/g;
	return($text);
}

# CRAWL
# Locate parent resources in nested pages. Returns an array of every matching
# path until the pattern is broken. SERVER SIDE ONLY
sub crawl {
	my @hits = ();
	return(@hits);
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page metadata 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# INFO
# Targeted 'info' metadata file parser
# Returns an array of three elements (title, alt, description)
sub info {
	my ($path) = @_;
	my @header = ();
	my @description = ();
	my $in_description = 0;
	open(INFO, $path) or return("", "", "");
	while (<INFO>) {
		s/\r?\n$//;
		if (!$in_description) {
			next if (!@header && /^\s*$/); # skip leading blank lines
			if (/^\s*$/) { $in_description = 1; next; }
			push(@header, $_);
		} else {
			push(@description, $_);
		}
	}
	close(INFO);
	if (!$in_description && @header > 1) {
		@description = splice(@header, 1); # v2 format: no blank line
	}
	shift(@description) while (@description && $description[0] =~ /^\s*$/);
	pop(@description)   while (@description && $description[-1] =~ /^\s*$/);
	my $alt = @header ? $header[0] : "";
	my $title   = (@header > 1) ? $header[1] : $alt;
	my $description = join("\n", @description);
	return($title, $alt, $description);
}

# PAGE TITLES
# Get untagged page title set from config, files or context
sub page_titles {
	my ($title, $alt) = ($PAGE_TITLE, $ALT_PAGE_TITLE); # "" unless configured
	my ($info_title, $info_alt) = info($INFO_FILE);
	$title = $info_title if ($title eq "");
	$alt   = $info_alt   if ($alt eq "");
	$alt   = $title if ($alt eq "");
	$alt   = $DEFAULT_PAGE_TITLE if ($alt eq "");
	return($title, $alt);
}

# METADATA TITLE
# Get META tagged page title
sub metadata_title {
	my @titles = page_titles();
	my $title = $titles[1];
	$title = "${title} - ${SITE_TITLE}" if ($SITE_TITLE);
	$title = "<TITLE>${title}</TITLE>\n";
	return($title);
}

# METADATA STYLE
# Link and package page styles from resource directory
sub metadata_style {
	my $style = "";
	return($style);
}

# GENERATE METADATA
# Generate site <head> data from configuration
sub generate_metadata {
	my $metadata = $STATIC_METADATA;
	# Get page description from config or file
	# Get page keywords from config or file
	# Get favicon from config or file
	$metadata .= metadata_title();
	$metadata .= metadata_style();
	return($metadata);
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page header 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# MEDITATION
# Display a random image above the page title from a configured path
sub meditate {
	my $meditation = "";
	return("") if (! -d $MEDITATION_DIR); # Meditations do not crawl
	opendir(MEDITATIONS,$MEDITATION_DIR) or return("");
	my @meditations = grep { /$IMAGE_FILETYPES/i && -f "${MEDITATION_DIR}/$_" } readdir(MEDITATIONS);
	closedir(MEDITATIONS);
	my $meditation_count = scalar @meditations;
	return("") if (!$meditation_count);
	my $selection = int(rand($meditation_count));
	$meditation = "$MEDITATION_DIR/$meditations[$selection]";
	$meditation = "<IMG SRC=\"${meditation}\" ALT=\"\" CLASS=\"meditation\">\n";
	return($meditation);
}

# PAGE TITLE
# Generate a page title from config, file, site or host context
sub page_title {
	my @titles = page_titles();
	my $title = $titles[0];
	return("") if (!$title);
	$title = "<H1><B>${title}</B></H1>\n";
	return($title);
}

# PAGE HEADER
# Assemble page header content including logo, title, meditation, etc.
sub page_header {
	my $header = "";
	my $title .= page_title();
	return("") if (!$title);
	$header = meditate();
	$header .= $title;
	return("") if (!$header);
	$header = "<CENTER>\n${header}</CENTER>\n" if ($CENTER_HEADER);
	$header = "<DIV ID=\"header\">\n${header}</DIV>\n";
	return($header);
}

# PAGE NAVIGATION
# Assemble page navigation breadcrumbs
sub page_navigation {
	my $navigation = "";
	return($navigation);
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Special elements 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# RULE
# Insert a horizontal rule based on configuration
sub rule {
	return("") if (!$AUTO_HR || (!$_NSI_HEADER && !$_NSI_CONTENT));
	return("<HR CLASS=\"rule\">\n");
}

# PAGE INTRO
# Display a configured HTML snippet above all non-header special elements
sub page_intro {
	my $intro = "";
	if (-f $INTRO_FILE && open(INTRO, $INTRO_FILE)) {
		$intro .= $_ while (<INTRO>);
		close(INTRO);
	}
	return("") if (!$intro);
	$intro = rule() . "<DIV ID=\"intro\">\n${intro}</DIV>\n";
	return($intro);
}

# TABLE OF CONTENTS
# Build a site table of contents to child directories from metadata files 
sub table_of_contents {
	my $toc = "";
	return($toc);
}

# PAGE LINKS
# Assemble a config-specified list of links to external sites and resources
sub page_links {
	my $links =  "";
	return($links);
}

# TRANSFORM
# Apply special transformations to tags and other objects
sub transform {
	my ($source) = @_;
	return($source);
};

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page body 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# BODY FRAGMENTS
# Get alphabetically ordered array of body fragment files in configured path
sub body_fragments {
	my @fragments = ();
	opendir(FRAGMENTS, $BODY_DIR) or return(@fragments);
	@fragments = sort grep { !/^\./ && -f "${BODY_DIR}/$_" } readdir(FRAGMENTS);
	closedir(FRAGMENTS);
	return(@fragments);
}

# BODY FRAGMENT
# Parse body fragment, determine if executable
sub body_fragment {
	my ($name) = @_;
	my $path = "${BODY_DIR}/${name}";
	my $fragment = "";
	open(FRAGMENT,$path) or return($fragment);
	my $shebang = <FRAGMENT>;
	my $options = <FRAGMENT>;
	close(FRAGMENT);
	# Return raw contents unless executable and with shebang on line 1
	if (!(-x $path && $shebang =~ /^#!/)) {
		open(FRAGMENT,$path) or return($fragment);
		$fragment .= $_ while (<FRAGMENT>);
		close(FRAGMENT);
		return($fragment);
	}
	# Attempt to gather title and wrap overrides from line 2 if commented
	$options  = "" if (!defined($options) || $options !~ /^#/);
	my $title = ($options =~ /title\s*=\s*"([^"]*)"/i) ? $1 : "";
	my $wrap  = $WRAP_SCRIPT_OUTPUT;
	$wrap = 1 if ($options =~ /\bwrap\b/i);
	$wrap = 0 if ($options =~ /\bno\s*wrap\b/i);
	$fragment = run_fragment($path);
	return("") if (!$fragment);
	$fragment = "<PRE>\n${fragment}</PRE>\n" if ($wrap);
	$fragment = "<H2>${title}</H2>\n${fragment}" if ($title);
	return $fragment;
}

# RUN FRAGMENT
# Run executable fragment with exec() in a child process and return the output
# Runs under Unix only! Script fragments on Windows and others silently fail.
sub run_fragment {
	my ($path) = @_;
	my $output = "";
	my $pid = open(SCRIPT,"-|");
	return ($output) if (!defined($pid));
	if (!$pid) { exec($path) or exit(127); } 
	$output .= $_ while (<SCRIPT>);
	close(SCRIPT);
	return($output);	
}

# PAGE BODY
# Render page body from supplied elements
sub page_body {
	my $body = "";
	# Standalone body file is always displayed first if present
	if (-f $BODY_FILE && open(BODY, $BODY_FILE)) {
		$body .= $_ while (<BODY>);
		close (BODY);
	}
	# Layer fragments in alphabetical order
	foreach my $fragment (body_fragments()) {
		$body .= body_fragment($fragment);
	}
	return("") if (!$body);
	$body = rule() . "<DIV ID=\"body\">\n${body}</DIV>\n";
	return($body);
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page footer
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# PAGE FOOTER
# Render page footer from configuration
sub page_footer {
	my $footer = "";
	return($footer);
}

# BEGIN PAGE GENERATION #######################################################
$_NSI_CONTENT = "";
$_NSI_PAGE    = "Content-type: text/html\n\n";
# -----------------------------------------------------------------------------
$_NSI_PAGE    .= "<!DOCTYPE ${HTML_DOCTYPE}>\n";
$_NSI_PAGE    .= "<!-- NSI ${version} -->\n";
$_NSI_PAGE    .= "<HTML>\n";
$_NSI_PAGE    .= "<HEAD>\n";
$_NSI_PAGE    .= generate_metadata();
$_NSI_PAGE    .= "</HEAD>\n";
$_NSI_PAGE    .= "<BODY>\n";
$_NSI_HEADER   = page_header();
$_NSI_HEADER  .= page_navigation() if ($NAV_POSITION eq "top");
$_NSI_CONTENT .= page_intro();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "top");
$_NSI_CONTENT .= page_body();
$_NSI_CONTENT .= page_links();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "bottom");
$_NSI_FOOTER .= page_navigation() if ($NAV_POSITION eq "bottom");
$_NSI_FOOTER .= page_footer();
if (!$_NSI_CONTENT) {
	$_NSI_CONTENT .= "<CENTER>\n";
	$_NSI_CONTENT .= "<I>This page (un)intentionally left blank</I>\n";
	$_NSI_CONTENT .= "</CENTER>\n";
}
$_NSI_CONTENT  = $_NSI_HEADER . $_NSI_CONTENT . $_NSI_FOOTER;
$_NSI_CONTENT  = transform($_NSI_CONTENT) if ($_NSI_CONTENT);
$_NSI_PAGE    .= "<DIV ID=\"content\">\n$_NSI_CONTENT</DIV>\n"; 
$_NSI_PAGE    .= "</BODY>\n";
$_NSI_PAGE    .= "</HTML>\n";
# -----------------------------------------------------------------------------
print $_NSI_PAGE if ($_NSI_CONTENT);
