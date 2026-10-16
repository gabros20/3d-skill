# Brief Lexicon

Purpose: Give the production terms that change what gets built, so briefs and shot lists say something checkable.

Read when:
- Writing brief sections, shot rows or lighting and material notes.
- A user term is ambiguous ("dramatic", "close", "glossy") and must become a parameter.

Skip when:
- Converting terms to renderer numbers (→ [refspec-mapping](refspec-mapping.md)).

Inputs:
- The term or brief section being written.

Produces:
- Precise wording for the brief; no artifact.

## Shot size and framing

By information shown: EWS/establishing (geography, scale) · WS (whole subject in setting) · MWS · MS · MCU · CU (detail) · ECU/insert (one decisive feature). For objects, name the visible surfaces and one scale cue. Product hero default: three-quarter view; commercial packshots fill roughly 80-85% of the frame.

## Angle, height, roll

Angle and height are independent: eye, low, high, overhead, worm's-eye; three-quarter, profile, front. Roll tilts the horizon (dutch): keep level unless motivated.

## Lens (full-frame equivalent)

14-24 ultra-wide (distortion, drama, close approach) · 28-35 wide (environment) · 50 normal · 85-135 portrait/hero compression · 150+ flat tele. **Position sets perspective; focal length sets framing**: a longer lens from farther away flattens, a wider lens up close exaggerates. three.js FOV is vertical, from a 24 mm sensor height (the `shots.json` convention; see [refspec-mapping](refspec-mapping.md)): `2·atan(12/f)`. DOF off by default on mobile.

## Moves

static · pan/tilt (pivot) · dolly or push-in/pull-out (translate on axis, parallax) · truck/pedestal (sideways/vertical) · crane (arc plus height) · orbit/turntable · handheld (noise) · whip · rack focus · dolly zoom. Motivate every move. Ease-in-out for moves, linear for turntable loops. One primary move per shot.

## Lighting

- **Key** shapes form; **fill** lifts shadow, ratio in stops (2:1 is one stop); negative fill removes light with black flags; **rim/back/kicker** separate edges; **practicals** are in-frame sources.
- Hard vs soft is source **size** relative to subject, not power.
- High-key (bright, low ratio) vs low-key (dark, high ratio). Warm tungsten about 3200 K, daylight about 5600 K; mixed warm and cool gives depth.
- Falloff is inverse-square: moving a light changes its ratio fast.
- Three-point is a start; describe the visible result instead.
- Gloss needs controlled reflections (strip softboxes, black flags); transparent subjects need edge or backlight.
- Real-time shorthand: HDRI for ambient and reflection, one directional for shadow, baked AO.

## Colour

Roles by share: dominant about 60, support 30, accent 10. Value structure (squint test) before hue. Tone mapping: AgX filmic, Khronos PBR Neutral for product accuracy, ACES punchier with hue skew. Colour space: sRGB for web output, linear working space. Grade: lift/gamma/gain or a LUT. Glow only on emissive surfaces.

## Materials (metal-rough PBR)

Base colour · metalness (0 or 1) · roughness · normal or bump · AO · emissive · clearcoat · transmission with IOR (glass, expensive) · sheen · anisotropy (brushed) · subsurface (wax, skin). Finishes: anodised, brushed, satin, polished, frosted, matte rubber.

## Animation principles that matter for objects and cameras

Timing and spacing · slow-in/slow-out · arcs · anticipation · follow-through and overlap · staging · secondary action · exaggeration (a dial). Squash and stretch is rare for hard products. Web motion: duration scales with distance, stagger with rests, cap simultaneous moving groups, loop seam = first frame equals last with matched velocity.

## FX

Particles (instanced points or sprites) · volumetrics and god-rays · fog · bloom · DOF/bokeh · motion blur · chromatic aberration · grain · vignette · SSAO · SSR · dissolve and mask reveals · scan lines · displacement. Each costs fill rate: [shared-performance](shared-performance.md).

## Production words

style frame (still of the final look) · storyboard · animatic (timed boards) · previs (greybox with camera) · techvis · lookdev · layout · plate · pass/AOV · comp · hero vs proxy asset · LOD · bake · retopo.
