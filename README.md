# shrinkwrap

Thinking about how to find a polygon the shrink wraps a group of rects.

# NOTES

## shrinkwap.py

This is working to do the project a side of a rect out until it hits another
rect. Should probably make more generic.


## origin

At the moment working out a way to project a side of a rect out until
collision. Thinking there should be a way to expand this projected rect to sort
of flood fill, discover the empty space.

This empty space finding is due to thinking about a better way to randomly
place rects, without just placing it and testing for collision. If we know the
empty spaces that are big enough to place a rect, we don't have to
loop-test-break, possibly never breaking if the rect won't fit.

This all started because I wanted to shrink wrap a polygon around randomly
placed rects.
