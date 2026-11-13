// SPDX-License-Identifier: GPL-3.0-or-later
#include <cstdlib>
#include <iostream>

#include "src/terminal/terminalframebuffer.h"

static void require( bool condition, const char* message )
{
  if ( !condition ) {
    std::cerr << message << std::endl;
    std::exit( EXIT_FAILURE );
  }
}

int main()
{
  using Terminal::Renditions;
  Renditions normal( 0 );
  Renditions dim( 0 );
  dim.set_rendition( 2 );
  require( dim.get_attribute( Renditions::faint ), "SGR 2 must set faint" );
  require( !( dim == normal ), "Screen comparisons must distinguish faint" );
  require( dim.sgr() == "\033[0;2m", "Redisplay must emit SGR 2" );

  dim.set_rendition( 1 );
  require( dim.sgr() == "\033[0;1;2m", "Bold and faint may coexist" );
  dim.set_rendition( 3 );
  dim.set_rendition( 4 );
  dim.set_rendition( 31 );
  dim.set_rendition( 22 );
  require( !dim.get_attribute( Renditions::bold ) && !dim.get_attribute( Renditions::faint ),
           "SGR 22 must clear bold and faint" );
  require( dim.sgr() == "\033[0;3;4;31m", "SGR 22 must preserve other attributes and colors" );

  dim.set_rendition( 2 );
  dim.set_rendition( 0 );
  require( dim == normal && dim.sgr() == "\033[0m", "SGR 0 must clear faint and colors" );

  dim.set_foreground_color( Renditions::make_true_color( 120, 130, 140 ) );
  dim.set_rendition( 2 );
  require( dim.sgr() == "\033[0;2;38;2;120;130;140m", "Faint must preserve true color" );
  return EXIT_SUCCESS;
}
