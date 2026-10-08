#!/usr/bin/env perl
###############################################################################
# NSI: The New Standard Index       #                                         #
my $version = '4.0.0';              #  A composer engine for simple websites  #
my $author  = 'ict@nfinit.systems'; #                                         #
###############################################################################

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Site configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Metadata defaults
$HTML_DOCTYPE="html";
$STATIC_METADATA="";

# Presentation defaults
$NAV_POSITION="top";
$TOC="bottom";

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page metadata 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# GENERATE METADATA
# Generate site <head> data from configuration
sub generate_metadata {
	my $metadata = "";
	return($metadata);
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Page header 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# PAGE HEADER
# Assemble page header content including logo, title, meditation, etc.
sub page_header {
	my $header = "";
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

# PAGE INTRO
# Display a configured HTML snippet above all non-header special elements
sub page_intro {
	my $intro = "";
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
	my $links = "";
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

# PAGE BODY
# Render page body from supplied elements
sub page_body {
	my $body = "";
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
$_NSI_PAGE    .= $STATIC_METADATA;
$_NSI_PAGE    .= "</HEAD>\n";
$_NSI_PAGE    .= "<BODY>\n";
$_NSI_CONTENT .= page_header();
$_NSI_CONTENT .= page_navigation() if ($NAV_POSITION eq "top");
$_NSI_CONTENT .= page_intro();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "top");
$_NSI_CONTENT .= page_body();
$_NSI_CONTENT .= page_links();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "bottom");
$_NSI_CONTENT .= page_navigation() if ($NAV_POSITION eq "bottom");
$_NSI_CONTENT .= page_footer() if ($_NSI_CONTENT);
$_NSI_CONTENT  = transform($_NSI_CONTENT) if ($_NSI_CONTENT);
if (!$_NSI_CONTENT) {
	$_NSI_CONTENT .= "<CENTER>\n";
	$_NSI_CONTENT .= "<I>This page (un)intentionally left blank</I>\n";
	$_NSI_CONTENT .= "</CENTER>\n";
}
$_NSI_PAGE    .= "<DIV ID=\"content\">\n$_NSI_CONTENT</DIV>\n"; 
$_NSI_PAGE    .= "</BODY>\n";
$_NSI_PAGE    .= "</HTML>\n";
# -----------------------------------------------------------------------------
print $_NSI_PAGE if ($_NSI_CONTENT);
