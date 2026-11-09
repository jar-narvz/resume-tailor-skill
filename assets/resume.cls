%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% resume.cls -- one-page, single-column resume class
%   - Times-style serif, 10pt body, 16pt name, half-inch margins
%   - Bold uppercase section headers with a full-width rule
%   - Tight bullets, small vertical spacing, optional fill-to-bottom mode
%   - ATS-safe text layer: no ligatures, real space characters, embedded fonts
% Compile with xelatex. Every tailored resume uses this class unchanged;
% nothing here varies per posting.
%
% Class options (pick one font):
%   termes        (default) TeX Gyre Termes, a free Times clone that ships
%                 with TeX Live and MacTeX
%   times-system  Times New Roman from the fonts installed on your system
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/11/08 v2.0 resume-tailor-skill resume class]

\newif\ifr@systemtimes \r@systemtimesfalse
\DeclareOption{termes}{\r@systemtimesfalse}
\DeclareOption{times-system}{\r@systemtimestrue}
\DeclareOption*{\PackageWarning{resume}{Unknown option '\CurrentOption'}}
\ProcessOptions\relax

\LoadClass[10pt,letterpaper]{article}

\RequirePackage[margin=0.5in]{geometry}
% XeLaTeX embeds a font subset with a Unicode map so ATS parsers read real
% characters. Common ligatures are off so "fi"/"fl" extract as two letters.
\RequirePackage{fontspec}
\ifr@systemtimes
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
\RequirePackage{enumitem}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{titlesec}
\RequirePackage{parskip}

\pagestyle{empty}
\linespread{0.97}\selectfont
\setlength{\parskip}{0pt}
\raggedbottom
% No hyphenation: split words read badly and break keyword matching in ATS.
\hyphenpenalty=10000
\exhyphenpenalty=10000
\emergencystretch=2em

% Section headers: bold uppercase + full-width rule
\titleformat{\section}%
  {\normalfont\bfseries\uppercase}%
  {}{0em}{}[\vspace{-7pt}\rule{\linewidth}{0.4pt}]
\titlespacing{\section}{0pt}{7pt plus 6pt}{4pt plus 1pt}

% Tight bullet list
\newenvironment{rBullets}{%
  \begin{itemize}[leftmargin=1.5em, topsep=1pt plus 1pt, itemsep=1pt plus 1.5pt, parsep=0pt, partopsep=0pt]
}{%
  \end{itemize}\vspace{3.5pt plus 4pt}
}

% Fill mode: the build script turns this on when a tailored resume leaves
% a small gap at the bottom. The stretchable glue above (section spacing,
% space after each bullet list, a little between bullets) then spreads
% evenly so the page ends at the bottom margin instead of in white space.
% At natural size (the default) all that glue is the plain spacing.
\newcommand{\rFillPage}{\flushbottom}
\newcommand{\rEndPage}{\par\pagebreak}

% Real space characters in the PDF text layer. XeTeX normally writes word
% gaps as cursor moves, and parsers that don't infer spaces from gaps glue
% words together ("SchoolExpected"). With this, every visible space is a
% U+0020 glyph. The look of the page doesn't change.
\XeTeXinterwordspaceshaping=2
\frenchspacing
\count255=`A \loop\sfcode\count255=1000 \ifnum\count255<`Z \advance\count255 by 1 \repeat
\sfcode"2013=1000 \sfcode"2014=1000
% \rS: a real space. \rSep: " | " separator. The \kern0pt on both sides
% keeps neighboring \href links from merging into one link annotation.
\newcommand{\rS}{\char32\relax\ignorespaces}
\newcommand{\rSep}{\kern0pt\char32|\char32\kern0pt\relax\ignorespaces}
\AtBeginDocument{%
  \let\rHfillOrig\hfill\renewcommand{\hfill}{\char32\relax\rHfillOrig}%
  \renewcommand{\labelitemi}{\textbullet\rlap{\char32}}}

% Header block
\newcommand{\rName}[1]{{\centering{\fontsize{16}{19}\selectfont\bfseries #1}\par}\vspace{3pt}}
\newcommand{\rContact}[1]{{\centering #1\par}}

% Education: bold school, right-aligned graduation; italic degree below
\newcommand{\rSchool}[2]{\textbf{#1} \hfill #2\par}
\newcommand{\rDegree}[1]{\textit{#1}\par}

% Experience, role first: bold title + italic dates, then italic org + location
\newcommand{\rTitle}[2]{\textbf{#1} \hfill \textit{#2}\par}
\newcommand{\rAt}[2]{\textit{#1} \hfill \textit{#2}\par}

% Projects. \rProject{title}{tech}{context}{term}: context is optional
% (e.g. "Course Project"); the build script writes link/demo headers itself.
\newcommand{\rProject}[4]{\textbf{#1\if\relax\detokenize{#2}\relax\else\ (#2)\fi}%
  \if\relax\detokenize{#3}\relax\else\rSep\textit{#3}\fi \hfill \textit{#4}\par}

% Skills line: bold label, items
\newcommand{\rSkill}[2]{\textbf{#1:}\rS #2\par}
