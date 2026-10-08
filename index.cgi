#!/usr/bin/env perl
###############################################################################
# NSI: The New Standard Index       #                                         #
my $version = '4.0.0.5';            #  A composer engine for simple websites  #
my $author  = 'ict@nfinit.systems'; #                                         #
###############################################################################

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
# Avoid editing this file! Direct changes are easily overwritten by updates,  #
# all of these variables are configurable externally                          #
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Site configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# System paths
$SYSTEM_DIR        = "sys";
$CONFIG_FILE       = "${SYSTEM_DIR}/config"; # Primary config file

################# FOR NESTED-SITE DEPLOYMENTS:
$SITE_ROOT = 0; # Configure this to 1 to prevent this page and its children
################# from inheriting configuration settings from any NSI parents

# Default special file paths
$INFO_FILE         = 'info'; # Page info file for title, TOC and description
$RESOURCE_DIR      = 'res'; # icons, styles and other page cosmetics
$FAVICON_FILE      = '${RESOURCE_DIR}/favicon.ico';
$LOGO_FILE         = '${RESOURCE_DIR}/logo'; # NSI detects extension
$MEDITATION_DIR    = '${RESOURCE_DIR}/meditations';
$STYLE_DIR         = '${RESOURCE_DIR}/style'; # Linked CSS stylesheets
$LEGACY_STYLE_DIR  = '${STYLE_DIR}/legacy'; # Direct-injected legacy CSS
$SCRIPT_DIR        = '${RESOURCE_DIR}/scripts'; # Linked client scripts
$LEGACY_SCRIPT_DIR = '${SCRIPT_DIR}/legacy'; # Direct-injected legacy scripts
$IMAGE_DIR         = 'img';
$INTRO_FILE        = 'intro.html';
$BODY_FILE         = 'body.html'; # single-file body, displays before fragments
$BODY_DIR          = 'body';     # fragmented body files and executables

# HTML 4.01 transitional DOCTYPE assists newer browsers with legacy syntax
$HTML_DOCTYPE    = "HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\"";

# Static metadata for all NSI pages
$STATIC_METADATA = <<EOF;
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<META NAME="viewport" CONTENT="width=device-width, initial-scale=1.0">
EOF

# Metadata defaults
$DEFAULT_PAGE_TITLE = "Untitled";
$PAGE_TITLE         = "";
$ALT_PAGE_TITLE     = ""; # Short title for ToC listings and meta
$PAGE_DESCRIPTION   = "";
$PAGE_KEYWORDS      = "";
$SITE_TITLE         = "";
$ORG_NAME           = ""; # Useful for server landing pages

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

# Keys a page only takes from its own config, never from a parent's
%LOCAL_KEYS = (SITE_ROOT => 1, PAGE_TITLE => 1, ALT_PAGE_TITLE => 1);

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

# DIRECTORY FILES
# Names of the files in a directory that match a pattern, in ls order.
# Hidden files (editor swap files and the like) and subdirectories are skipped.
sub directory_files {
	my ($dir, $pattern) = @_;
	my @files = ();
	opendir(LISTING, $dir) or return(@files);
	@files = sort grep { !/^\./ && /$pattern/i && -f "${dir}/$_" } readdir(LISTING);
	closedir(LISTING);
	return(@files);
}

# READ FILE
# Whole contents of a file, or "" if it can't be read
sub read_file {
	my ($path) = @_;
	my $text = "";
	open(FILE, $path) or return($text);
	$text .= $_ while (<FILE>);
	close(FILE);
	return($text);
}

# PARENT DIRECTORY
# Trim the last component from a path as text (never follows symlinks)
# Example: parent_dir("/www/page") returns "/www"
sub parent_dir {
	my ($dir) = @_;
	$dir =~ s/\/[^\/]*$//;
	$dir = "/" if ($dir eq "");
	return($dir);
}

# WEB ROOT
# The directory that serves this request's URL root: strip the path
# components that SCRIPT_NAME and SCRIPT_FILENAME have in common
sub web_root {
	my ($file, $url) = @_;
	my @file = split(/\//, $file);
	my @url  = split(/\//, $url);
	pop(@file); pop(@url); # drop the script name from both
	while (@url && @file && $url[-1] eq $file[-1]) {
		pop(@url); pop(@file);
	}
	return(join("/", @file) || "/");
}

# SITE ROOT AT
# Does the config in this directory set SITE_ROOT? (read before any
# config is applied, so it can't come from a parent)
sub site_root_at {
	my ($dir) = @_;
	my $site_root = 0;
	open(PEEK, "${dir}/${CONFIG_FILE}") or return(0);
	while (<PEEK>) {
		$site_root = $1 if (/^\s*site_root\s*=\s*(.*?)\s*$/i);
	}
	close(PEEK);
	return($site_root ? 1 : 0);
}

# BUILD CHAIN
# Directories this page inherits from, nearest first. Inside the web root,
# directories without NSI files are passed through; beyond it, the chain
# only continues through NSI pages. SITE_ROOT=1 ends it anywhere.
sub build_chain {
	my @chain = ();
	my $dir = $_NSI_PAGE_DIR;
	my $past_web_root = 0;
	while (1) {
		push(@chain, $dir);
		last if (site_root_at($dir));
		$past_web_root = 1 if ($dir eq $_NSI_WEB_ROOT);
		my $parent = parent_dir($dir);
		last if ($parent eq $dir);
		# Check for NSI engine files beyond the web root, to allow
		# resourcing to work for pages with vanity subdomains
		last if ($past_web_root && ! -f "${parent}/${_NSI_SCRIPT}");
		$dir = $parent;
	}
	return(@chain);
}

# CRAWL
# Look for identical copies of a file or directory along the page's chain
# Nearest/local files first
sub crawl {
	my ($path) = @_;
	my @hits = ();
	return(@hits) if ($path eq "");
	foreach my $dir (@_NSI_CHAIN) {
		my $hit = ($dir eq "/") ? "/${path}" : "${dir}/${path}";
		push(@hits, $hit) if (-e $hit);
	}
	return(@hits);
}

# URL FOR
# Get a relative URL for a path based on the page chain, returns nothing
# if the resource is beyond the web root
sub url_for {
	my ($path) = @_;
	for (my $i = 0; $i <= $#_NSI_CHAIN; $i++) {
		my $dir = $_NSI_CHAIN[$i];
		next if (index($path, "${dir}/") != 0);
		return("") if ($i > $_NSI_WEB_ROOT_STEP);
		return(("../" x $i) . substr($path, length($dir) + 1));
	}
	return("");
}

# READ CONFIG
# Override existing defaults from a KEY=VALUE file. Keys are the names of
# the variables they set, in any case; unknown keys are ignored. Keys in
# %LOCAL_KEYS are only taken from the page's own config.
sub read_config {
	my ($path) = @_;
	my $local = ($path eq "${_NSI_PAGE_DIR}/${CONFIG_FILE}"); # page's own config
	open(CONFIG, $path) or return;
	while (<CONFIG>) {
		next if (/^\s*(#|$)/);
		next if (!/^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
		my ($key, $value) = (uc($1), $2);
		next if ($key eq "SYSTEM_DIR" || $key eq "CONFIG_FILE");
		next if (!$local && $LOCAL_KEYS{$key});
		next if (!defined(${"main::${key}"}));
		${"main::${key}"} = $value;
	}
	close(CONFIG);
}

# EXPAND SETTINGS
# Fill in ${NAME} placeholders in settings once all configs are applied.
# Repeats so placeholders built on other placeholders resolve too.
sub expand_settings {
	foreach my $key (keys %main::) {
		next if ($key !~ /^[A-Z][A-Z0-9_]*$/);
		next if (!defined(${"main::${key}"}));
		for (my $pass = 0; $pass < 5; $pass++) {
			last if (${"main::${key}"} !~ s/\$\{([A-Z][A-Z0-9_]*)\}/defined(${"main::$1"}) ? ${"main::$1"} : "\${$1}"/ge);
		}
	}
}

# CONFIGURE PAGE
# Apply every config on the chain, top first, so the nearest one wins,
# then fill in ${NAME} placeholders
sub configure_page {
	foreach my $config (reverse(crawl($CONFIG_FILE))) {
		read_config($config);
	}
	expand_settings();
}

# RESOLVE RUNTIME
# Resolves the runtime environment of the current engine
sub resolve_runtime {
	my $file = $ENV{SCRIPT_FILENAME} || "";
	my $url  = $ENV{SCRIPT_NAME} || "";
	if ($file =~ /^\// && $url) {
		($_NSI_SCRIPT = $file) =~ s/^.*\///;
		$_NSI_PAGE_DIR = parent_dir($file);
		$_NSI_WEB_ROOT = web_root($file, $url);
	} else {
		# Not under a web server: this directory only (v1 mode)
		$_NSI_SCRIPT   = "index.cgi";
		$_NSI_PAGE_DIR = ".";
		$_NSI_WEB_ROOT = ".";
	}
	@_NSI_CHAIN = build_chain();
	$_NSI_WEB_ROOT_STEP = $#_NSI_CHAIN;
	for (my $i = 0; $i <= $#_NSI_CHAIN; $i++) {
		if ($_NSI_CHAIN[$i] eq $_NSI_WEB_ROOT) {
			$_NSI_WEB_ROOT_STEP = $i;
			last;
		}
	}
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
	# Legacy stylesheet inlining
	my ($style_dir, @files);
	# Choose the first legacy style directory with files present
	foreach my $candidate (crawl($LEGACY_STYLE_DIR)) {
		@files = directory_files($candidate, '\.css$');
		$style_dir = $candidate, last if (@files);
	}
	# Concatenate every CSS file into one block
	foreach my $stylesheet (@files) {
		my $css = read_file("${style_dir}/${stylesheet}");
		$css .= "\n" if ($css ne "" && $css !~ /\n$/);
		$style .= $css;
	}
	$style = "<STYLE TYPE=\"text/css\"><!--\n${style}//--></STYLE>\n" if ($style);
	# Stylesheet linking
	($style_dir, @files) = ("");
	foreach my $candidate (crawl($STYLE_DIR)) {
		@files = directory_files($candidate, '\.css$');
		$style_dir = $candidate, last if (@files);
	}
	foreach my $stylesheet (@files) {
		my $link = url_for("${style_dir}/${stylesheet}");
		next if ($link eq ""); # above the web root
		$style .= "<LINK REL=\"stylesheet\" TYPE=\"text/css\" HREF=\"${link}\" MEDIA=\"all\">\n";
	}
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
resolve_runtime();
configure_page();
# -----------------------------------------------------------------------------
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
