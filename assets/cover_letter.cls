%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% cover_letter.cls -- one-page cover letter that pairs with resume.cls
%   bold NAME / bold contact line / date / addressee block /
%   salutation / 3-4 body paragraphs / Sincerely, / signature / typed name
% Same fonts and options as resume.cls (termes default, or times-system)
% so the two PDFs read as a set. Compile with xelatex.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cover_letter}[2026/11/08 v2.0 resume-tailor-skill cover letter class]

\newif\ifcl@systemtimes \cl@systemtimesfalse
\DeclareOption{termes}{\cl@systemtimesfalse}
\DeclareOption{times-system}{\cl@systemtimestrue}
\DeclareOption*{\PackageWarning{cover_letter}{Unknown option '\CurrentOption'}}
\ProcessOptions\relax

\LoadClass[11pt,letterpaper]{article}
\RequirePackage[margin=1in]{geometry}
\RequirePackage{fontspec}
\ifcl@systemtimes
  \setmainfont{Times New Roman}[Ligatures={TeX,NoCommon}]
\else
  \setmainfont{texgyretermes}[
    Extension=.otf,
    UprightFont=*-regular,
    BoldFont=*-bold,
    ItalicFont=*-italic,
    BoldItalicFont=*-bolditalic,
    Ligatures={TeX,NoCommon}]
\fi
\RequirePackage[hidelinks]{hyperref}
\pagestyle{empty}
\frenchspacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{10pt}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\emergencystretch=2em
\raggedbottom
\XeTeXinterwordspaceshaping=2
\newcommand{\clSep}{\kern0pt\char32|\char32\kern0pt\relax\ignorespaces}

% Header: bold name, bold contact line
\newcommand{\clName}[1]{{\fontsize{16}{19}\selectfont\bfseries #1\par}\vspace{-8pt}}
\newcommand{\clContact}[1]{{\bfseries #1\par}}
% Address block: lines with no space between them
\newenvironment{clBlock}{\setlength{\parskip}{0pt}}{\par}
% Closing: Sincerely, / italic signature / typed name
\newcommand{\clClosing}[1]{\textbf{Sincerely,}\par\vspace{-4pt}\textit{#1}\par\vspace{-8pt}\textbf{#1}\par}
