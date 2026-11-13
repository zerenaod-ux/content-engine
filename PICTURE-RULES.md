# Content Engine: picture rules (owner feedback 2026-11-13)

## What the owner said
- Voice speed, music, background sound: GOOD, keep as they are.
- Pictures: NOT good. They look like shapes being "processed", not like real things working.
- Example: a microwave video must SHOW A MICROWAVE (door, window, turntable, light, buttons), the pizza on the plate inside, and the heat reaching the food the way it really happens. A drawing is fine, but it must be recognisable at a glance and detailed.

## The rules every video must follow
1. **The star is a real-looking object.** The main thing of the topic is drawn with its real parts (a library "prop" or a detailed drawing), never a plain box, circle or blob.
2. **Recognisable at a glance.** A viewer with the sound off must name the object in one second.
3. **Show the inside.** When the secret is inside (a machine, a body, the ground), use a cut-away so the viewer sees the inside working.
4. **Real process, real order.** Things move the way they really do: the plate turns, the light comes on, waves bounce, the food steams. No made-up symbols standing in for the real action.
5. **Rich detail.** Small real parts (buttons, vents, screws, crumbs, steam) make it believable. At least 3 visible details on the star.
6. **One clear stage.** Objects stand where they would in real life (a microwave on a kitchen counter, not on grass).
7. **Labels are short helpers only;** the picture explains, not the text.

## How the system enforces it
- `scene_lib/props.js`-style library inside `scene_lib/scene.html`: part type `prop` draws detailed real objects with moving parts (first ones: microwave, toaster, fridge, pizza, kettle, lamp, phone). The library grows over time.
- The checker rejects a scene whose step stars are plain shapes (rect, circle, ellipse, poly) and asks for a prop, an emoji or a detailed path.
- The writer is told: if a prop exists for the topic, use it.

## Status
- 2026-11-13: rules written; prop library started with the first objects; checker rule added. Next: more props (engine, heart, lungs, plant cell, car, plane, volcano, bridge...), one model scene built with props.
