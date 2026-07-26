// Surface crate: expands glue via m4 and links optional gated helpers.

#[cfg(all(feature = "lane_x", not(feature = "lane_y")))]
m4::weave!(1, 0);

#[cfg(all(feature = "lane_y", not(feature = "lane_x")))]
m4::weave!(0, 1);

#[cfg(all(feature = "lane_x", feature = "lane_y"))]
m4::weave!(1, 1);

#[cfg(not(any(feature = "lane_x", feature = "lane_y")))]
m4::weave!(0, 0);
