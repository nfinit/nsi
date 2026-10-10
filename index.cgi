#!/usr/bin/env perl
###############################################################################
# NSI: The New Standard Index       #                                         #
my $version = '4.0.0.13';           #  A composer engine for simple websites  #
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
$BODY_DIR          = 'body';      # fragmented body files and executables
$LINKS_FILE        = 'links';     # links to external websites
$GROUPS_FILE       = 'groups'; # Use this file to group/annotate items in a TOC

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
$ORG_URL            = "";
$COPYRIGHT_BEGIN    = "";

# Presentation defaults
$AUTO_HR            = 1; # Automatically separate sections with rules
$SUB_LOGO           = 0; # Show logo on subpages
$NAV_BARS	    = "local";
$NAV_POSITION       = "top";
$TOC                = "bottom";
$TOC_TITLE          = "";
$TOC_SUBTITLE       = "";
$LINKS_TITLE        = "";
$LINKS_SUBTITLE     = "";
$CENTER_HEADER      = 0;
$WRAP_SCRIPT_OUTPUT = 0; # Wrap executable fragments output in <PRE> tags
$IMAGE_FILETYPES    = '\.(gif|jpe?g|png)$';
$SHOW_COPYRIGHT     = 1;  # Only available when ORG_NAME is set 
$FOOTER_NAV         = 1;  # Enable footer navigation controls
$TIMESTAMP_FORMAT   = ""; # strftime format; empty = localtime (setting loads POSIX)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Universal helpers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Keys a page only takes from its own config, never from a parent's
%LOCAL_KEYS = (
	PAGE_DESCRIPTION => 1,
	PAGE_KEYWORDS => 1,
	SITE_ROOT => 1,
	NAV_ROOT => 1, 
	PAGE_TITLE => 1, 
	ALT_PAGE_TITLE => 1
);

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
	local $_;
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

# CONFIG FLAG AT
# Is a yes/no setting turned on in one directory's own config? Used for
# per-directory markers (SITE_ROOT, NAV_ROOT) that are never inherited.
sub config_flag_at {
	local $_;
	my ($dir, $key) = @_;
	my $flag = 0;
	open(PEEK, "${dir}/${CONFIG_FILE}") or return(0);
	while (<PEEK>) {
		$flag = $1 if (/^\s*\Q${key}\E\s*=\s*(.*?)\s*$/i);
	}
	close(PEEK);
	return($flag ? 1 : 0);
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
		last if (config_flag_at($dir,'SITE_ROOT'));
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
	my @paths = grep { $_ ne "" } @_;
	my @hits = ();
	foreach my $dir (@_NSI_CHAIN) {
		foreach my $path (@paths) {
			my $hit = ($dir eq "/") ? "/${path}" : "${dir}/${path}";
			push(@hits, $hit) if (-e $hit);
		}
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

# URL PATH
# Escape a file or directory name for use in a link
sub url_path {
	my ($path) = @_;
	$path =~ s/([^A-Za-z0-9_.~\/-])/sprintf("%%%02X", ord($1))/ge;
	return($path);
}

# READ CONFIG
# Override existing defaults from a KEY=VALUE file. Keys are the names of
# the variables they set, in any case; unknown keys are ignored. Keys in
# %LOCAL_KEYS are only taken from the page's own config.
sub read_config {
	local $_;
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
	local $_;
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
	$title = "${title} - ${SITE_TITLE}" if ($SITE_TITLE && ($title ne $SITE_TITLE));
	$title = plain_text($title);
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
	# Wrap in an HTML comment tag to prevent spillover on very old browsers
	$style = "<STYLE TYPE=\"text/css\"><!--\n${style}//--></STYLE>\n" if ($style);
	# Print rule: hide navigation and other no_print elements on paper
	$style .= "<STYLE TYPE=\"text/css\" MEDIA=\"print\"><!--\n.no_print { display: none; }\n//--></STYLE>\n";
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

# METADATA SCRIPTS
# Link and package client scripts from resource directory
sub metadata_scripts {
	my $scripts = "";
	# Legacy script inlining
	my ($script_dir, @files);
	foreach my $candidate (crawl($LEGACY_SCRIPT_DIR)) {
		@files = directory_files($candidate, '\.js$');
		$script_dir = $candidate, last if (@files);
	}
	# Concatenate legacy scripts into one block
	foreach my $script (@files) {
		my $fragment = read_file("${script_dir}/${script}");
		$fragment .= "\n" if ($fragment ne "" && $fragment !~ /\n$/);
		$scripts .= $fragment;
	}
	# Wrap in an HTML comment tag to prevent spillover on very old browsers
	$scripts = "<SCRIPT TYPE=\"text/javascript\" LANGUAGE=\"JavaScript\"><!--\n${scripts}//--></SCRIPT>\n"
		if ($scripts);
	# Script linking
	($script_dir, @files) = ("");
	foreach my $candidate (crawl($SCRIPT_DIR)) {
		@files = directory_files($candidate, '\.js$');
		$script_dir = $candidate, last if (@files);
	}
	foreach my $script (@files) {
		my $link = url_for("${script_dir}/${script}");
		next if ($link eq ""); # above the web root	
		$scripts .= "<SCRIPT TYPE=\"text/javascript\" LANGUAGE=\"JavaScript\" SRC=\"${link}\"></SCRIPT>\n";
	}
	return($scripts);
}
# GENERATE METADATA
# Generate site <head> data from configuration
sub generate_metadata {
	my $metadata = $STATIC_METADATA;
	# Description: configured, or the page's info description
	my $description = $PAGE_DESCRIPTION;
	$description = (info($INFO_FILE))[2] if ($description eq "");
	$description = plain_text($description);
	$metadata .= "<META NAME=\"description\" CONTENT=\"${description}\">\n"
		if ($description ne "");
	$metadata .= "<META NAME=\"keywords\" CONTENT=\"" . plain_text($PAGE_KEYWORDS) . "\">\n"
		if ($PAGE_KEYWORDS ne "");
	# Favicon: the nearest one the browser can reach
	foreach my $icon (crawl($FAVICON_FILE)) {
		my $url = url_for($icon);
		next if ($url eq "");
		$metadata .= "<LINK REL=\"shortcut icon\" TYPE=\"image/x-icon\" HREF=\"${url}\">\n";
		last;
	}
	$metadata .= metadata_title();
	$metadata .= metadata_style();
	$metadata .= metadata_scripts();
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

# PAGE LOGO
# Site/page title logo, locates the nearest compatibly named file with
# any extension listed in IMAGE_FILETYPES, or as named if extension specified
# explicitly.
sub page_logo {
	return("") if ($_NSI_WEB_ROOT_STEP > 0 && !$SUB_LOGO);
	my ($dir, $name) = ($LOGO_FILE =~ /^(.*)\/([^\/]+)$/) ? ($1, $2) : (".", $LOGO_FILE);
	my $pattern = '^' . quotemeta($name);
	$pattern .= ($name =~ /$IMAGE_FILETYPES/i) ? '$' : $IMAGE_FILETYPES;
	foreach my $candidate (crawl($dir)) {
		foreach my $file (directory_files($candidate, $pattern)) {
			my $url = url_for("${candidate}/${file}");
			return("<IMG SRC=\"${url}\" ALT=\"\" CLASS=\"logo\">") if ($url ne "");
		}
	}
	return("");
}

# PAGE HEADER
# Assemble page header content including logo, title, meditation, etc.
sub page_header {
	my $header = "";
	my $title = page_title();
	return("") if (!$title);
	my $logo = page_logo();
	$title = "<TABLE><TR>\n<TD>${logo}</TD>\n<TD>${title}</TD>\n</TR></TABLE>\n" if ($logo);
	$header = meditate();
	$header .= $title;
	return("") if (!$header);
	$header = "<CENTER>\n${header}</CENTER>\n" if ($CENTER_HEADER);
	$header = "<DIV ID=\"header\">\n${header}</DIV>\n";
	return($header);
}

# NAV ROOT STEP
# Step up the chain to the nearest NAV_ROOT page, or to the site home
sub nav_root_step {
	for (my $i = 0; $i < $_NSI_WEB_ROOT_STEP; $i++) {
		return($i) if (config_flag_at($_NSI_CHAIN[$i], "NAV_ROOT"));
	}
	return($_NSI_WEB_ROOT_STEP);
}

# NAV BAR
# Generate a navigation bar for the directory $step levels up
# Page itself, or sections containing it, in bold
sub nav_bar {
	my ($step) = @_;
	my $root = $_NSI_CHAIN[$step];
	my $up = "../" x $step;
	my @items = ();
	my ($title, $alt) = info("${root}/${INFO_FILE}");
	$alt = "Home" if ($alt eq "");
	push(@items, ($step == 0) ? "<I>${alt}</I>" : "<A HREF=\"${up}\">${alt}</A>");
	foreach my $entry (toc_entries($root)) {
		my ($name, $label) = @$entry;
		my $dir = "${root}/${name}";
		my $item = "<A HREF=\"${up}" . url_path($name) . "/\">${label}</A>";
		$item = "<I>${label}</I>" if ($dir eq $_NSI_CHAIN[0]);
		$item = "<B>${item}</B>" if (grep { $_ eq $dir } @_NSI_CHAIN[1 .. $step - 1]);
		push(@items, $item);
	}
	return("") if (@items < 2); # no sections to display
	return("<DIV>" . join(" | ", @items) . "</DIV>\n");
} 

# PAGE ROOT NAVIGATION
# Assemble page navigation bar, always pointing to the root TOC 
sub page_root_navigation {
	return (nav_bar($_NSI_WEB_ROOT_STEP));
}

# PAGE LOCAL NAVIGATION
# Assemble page navigation bar, always pointing to the nearest NAV_ROOT TOC 
sub page_local_navigation {
	return (nav_bar(nav_root_step()));
}

# PAGE NAVIGATION
# Assemble page navigation bar using root, local or both.

sub page_navigation {
	my $navigation = "";
	$navigation .= page_root_navigation()
		if ($NAV_BARS eq "root" || ($NAV_BARS eq "both" && nav_root_step() != $_NSI_WEB_ROOT_STEP));
	$navigation .= page_local_navigation() if ($NAV_BARS eq "local" || $NAV_BARS eq "both");
	return("") if (!$navigation);
	$navigation = "<DIV ID=\"navigation\" CLASS=\"no_print\">\n" . rule() . "${navigation}</DIV>\n";
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
	local $_;
	my $intro = "";
	if (-f $INTRO_FILE && open(INTRO, $INTRO_FILE)) {
		$intro .= $_ while (<INTRO>);
		close(INTRO);
	}
	return("") if (!$intro);
	$intro = rule() . "<DIV ID=\"intro\">\n${intro}</DIV>\n";
	return($intro);
}

# GROUP BLOCKS
# Groups declared in a directory's groups file, in file order. Blocks are
# separated by blank lines: an optional heading, optional description lines,
# then member directories, written with a trailing "/". A block that starts
# with a member has no heading (it only fixes the order). Each group is
# [heading, description, member, member, ...].
sub group_blocks {
	my ($dir) = @_;
	my @groups = ();
	my $text = read_file("${dir}/${GROUPS_FILE}");
	$text =~ s/\r//g;
	foreach my $block (split(/\n[ \t]*\n/, $text)) {
		my @lines = grep { /\S/ } split(/\n/, $block);
		s/^\s+//, s/\s+$// foreach (@lines);
		next if (!@lines);
		my $heading = ($lines[0] =~ /\/$/) ? "" : shift(@lines);
		my @members = map { substr($_, 0, -1) } grep { /\/$/ } @lines;
		my $description = join("\n", grep { !/\/$/ } @lines);
		push(@groups, [$heading, $description, @members]);
	}
	return(@groups);
}

# TOC ENTRIES
# Child directories of a directory that have an info file: first those
# declared in its groups file, in that order, then the rest sorted by short
# name. Each entry is [name, short name, description, group heading,
# group description, group number]; undeclared entries are group 0.
sub toc_entries {
	my ($dir) = @_;
	my (%found, @entries);
	opendir(CHILDREN, $dir) or return(@entries);
	my @names = grep { !/^\./ && -d "${dir}/$_" } readdir(CHILDREN);
	closedir(CHILDREN);
	foreach my $name (@names) {
		my $info = "${dir}/${name}/${INFO_FILE}";
		next if (! -f $info);
		my ($title, $alt, $description) = info($info);
		next if ($alt eq "");
		$found{$name} = [$name, $alt, $description];
	}
	my $number = 0;
	foreach my $group (group_blocks($dir)) {
		my ($heading, $description, @members) = @$group;
		$number++;
		foreach my $member (@members) {
			next if (!$found{$member});
			push(@entries, [@{$found{$member}}, $heading, $description, $number]);
			delete($found{$member});
		}
	}
	foreach my $entry (sort { lc($$a[1]) cmp lc($$b[1]) } values(%found)) {
		push(@entries, [@$entry, "", "", 0]);
	}
	return(@entries);
}

# TABLE OF CONTENTS
# List this page's child pages, with a heading and description above each
# declared group
sub table_of_contents {
	my ($toc, $list, $key, $heading, $description) = ("", "", "");
	foreach my $entry (toc_entries($_NSI_PAGE_DIR), undef) {
		my $next_key = "";
		if ($entry) {
			my ($name, $alt, $about, $group_heading, $group_description, $number) = @$entry;
			$next_key = ($group_heading ne "") ? $number : "plain";
			if ($next_key ne $key) {
				$toc .= toc_group($heading, $description, $list);
				($list, $key, $heading, $description) = ("", $next_key, $group_heading, $group_description);
			}
			my $item = "<H3><A HREF=\"" . url_path($name) . "/\">${alt}</A></H3>\n";
			$item .= "<P>${about}</P>\n" if ($about ne "");
			$list .= "<LI>\n${item}</LI>\n";
		} else {
			$toc .= toc_group($heading, $description, $list);
		}
	}
	return("") if (!$toc);
	$toc = "<P ID=\"toc_subtitle\">${TOC_SUBTITLE}</P>\n${toc}" if ($TOC_SUBTITLE);
	$toc = "<H2>${TOC_TITLE}</H2>\n${toc}" if ($TOC_TITLE);
	$toc = rule() . "<DIV ID=\"toc\">\n${toc}</DIV>\n";
	return($toc);
}

# TOC GROUP
# One run of TOC items: a plain list, or a headed group with its description
sub toc_group {
	my ($heading, $description, $list) = @_;
	return("") if ($list eq "");
	$list = "<UL>\n${list}</UL>\n";
	return($list) if ($heading eq "");
	$list = "<P CLASS=\"group_description\">${description}</P>\n${list}" if ($description ne "");
	return("<DIV CLASS=\"toc_group\">\n<H2>${heading}</H2>\n${list}</DIV>\n");
}

# LINK ENTRIES
# Entries from this page's links file, in file order. Entries are blocks
# separated by blank lines: a label, a URL, then an optional description.
# Each entry is [label, url, description]; blocks without a URL are skipped.
sub link_entries {
	my @entries = ();
	my $text = read_file($LINKS_FILE);
	$text =~ s/\r//g;
	foreach my $block (split(/\n[ \t]*\n/, $text)) {
		my @lines = grep { /\S/ } split(/\n/, $block);
		next if (@lines < 2);
		my ($label, $url, @description) = @lines;
		s/^\s+//, s/\s+$// foreach ($label, $url);
		next if ($url =~ /\s/); # line 2 is a sentence, not a URL
		push(@entries, [$label, $url, join("\n", @description)]);
	}
	return(@entries);
}

# PAGE LINKS
# Generate a list of links to external resources from a configured file 
sub page_links {
	my $links = "";
	foreach my $entry (link_entries()) {
		my ($label, $url, $description) = @$entry;
		$url =~ s/"/%22/g;
		my $item = "<H3><A HREF=\"${url}\">${label}</A></H3>\n";
		$item .= "<P>${description}</P>\n" if ($description ne "");
		$links .= "<LI>\n${item}</LI>\n";
	}
	return("") if (!$links);
	$links = "<UL>\n${links}</UL>\n";
	$links = "<P ID=\"links_subtitle\">${LINKS_SUBTITLE}</P>\n${links}" if ($LINKS_SUBTITLE);
	$links = "<H2>${LINKS_TITLE}</H2>\n${links}" if ($LINKS_TITLE);
	$links = rule() . "<DIV ID=\"links\">\n${links}</DIV>\n";
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
	local $_;
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
	foreach my $part (split(/;/, $options)) {
		$wrap = 1 if ($part =~ /^\s*#?\s*wrap\s*$/i);
		$wrap = 0 if ($part =~ /^\s*#?\s*no\s*wrap\s*$/i);
	}
	$fragment = run_fragment($path);
	return("") if (!$fragment);
	$fragment = "<PRE CLASS=\"script_output\">\n${fragment}</PRE>\n" if ($wrap);
	$fragment = "<H2>${title}</H2>\n${fragment}" if ($title);
	return $fragment;
}

# RUN FRAGMENT
# Run executable fragment with exec() in a child process and return the output
# Runs under Unix only! Script fragments on Windows and others silently fail.
sub run_fragment {
	local $_;
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
	local $_;
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

# FOOTER NAVIGATION
# Generates back to top, nearest parent page and home page controls
sub footer_navigation {
	return("") if (!$FOOTER_NAV);
	my @links = ("<A HREF=\"#top\">Back to top</A>");
	my $home = $_NSI_WEB_ROOT_STEP;
	if ($home > 0) {
		# Nearest parent that is an NSI page (skips plain directories)
		my $parent = 1;
		$parent++ while ($parent < $home && ! -f "$_NSI_CHAIN[$parent]/$_NSI_SCRIPT");
		if ($parent < $home) {
			my ($title, $alt) = info("$_NSI_CHAIN[$parent]/$INFO_FILE");
			$alt = "Up" if ($alt eq "");
			push(@links, "<A HREF=\"" . ("../" x $parent) . "\">${alt}</A>");
		}
		my ($title, $alt) = info("$_NSI_CHAIN[$home]/$INFO_FILE");
		$alt = "Home" if ($alt eq "");
		push(@links, "<A HREF=\"" . ("../" x $home) . "\">${alt}</A>");
	}
	return("<SPAN CLASS=\"no_print\">" . join(" | ", @links) . "</SPAN>");
}

# PAGE FOOTER
# Render page footer from configuration
sub page_footer {
	my $stamp = scalar(localtime());
	if ($TIMESTAMP_FORMAT) {
		require POSIX; # loaded only when asked for: it doubles the page time
		$stamp = POSIX::strftime($TIMESTAMP_FORMAT, localtime());
	}
	my $left = "<SPAN CLASS=\"timestamp\">${stamp}</SPAN>";
	if ($COPYRIGHT_BEGIN || $ORG_NAME) {
		my $year = (localtime())[5] + 1900;
		my $years = $year;
		$years = "${COPYRIGHT_BEGIN} - ${year}" if ($COPYRIGHT_BEGIN && $COPYRIGHT_BEGIN ne $year);
		my $owner = $ORG_NAME;
		$owner = "<A HREF=\"${ORG_URL}\">${owner}</A>" if ($owner && $ORG_URL);
		$left .= "<BR>\n<SPAN CLASS=\"copyright\">(C) ${years} ${owner}</SPAN>" if ($SHOW_COPYRIGHT);
	}
	my $right = footer_navigation();
	my $footer = "<TR>\n<TD ALIGN=\"LEFT\">${left}</TD>\n<TD ALIGN=\"RIGHT\">${right}</TD>\n</TR>\n";
	$footer = "<TABLE WIDTH=\"100%\">\n${footer}</TABLE>\n";
	$footer = rule() . "<DIV ID=\"footer\">\n${footer}</DIV>\n";
	return($footer);
}

# BEGIN PAGE GENERATION #######################################################
resolve_runtime();
configure_page();
# -----------------------------------------------------------------------------
$_NSI_CONTENT = "";
$_NSI_PAGE    = "Content-type: text/html; charset=UTF-8\n\n";
# -----------------------------------------------------------------------------
$_NSI_PAGE    .= "<!DOCTYPE ${HTML_DOCTYPE}>\n";
$_NSI_PAGE    .= "<!-- NSI ${version} -->\n";
$_NSI_PAGE    .= "<HTML>\n";
$_NSI_PAGE    .= "<HEAD>\n";
$_NSI_PAGE    .= generate_metadata();
$_NSI_PAGE    .= "</HEAD>\n";
$_NSI_PAGE    .= "<BODY>\n<A NAME=\"top\"></A>\n";
$_NSI_HEADER   = page_header();
$_NSI_HEADER  .= page_navigation() if ($NAV_POSITION eq "top");
$_NSI_CONTENT .= page_intro();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "top");
$_NSI_CONTENT .= page_body();
$_NSI_CONTENT .= table_of_contents() if ($TOC eq "bottom");
$_NSI_CONTENT .= page_links();
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
