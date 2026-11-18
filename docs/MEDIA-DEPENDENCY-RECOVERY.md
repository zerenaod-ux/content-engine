# Media dependency recovery

The first cloud verification after the daily persistence/scope changes was cancelled at its ten-minute limit while apt was fetching media dependencies; its tests never ran. This was not a successful verification or a new generated video.

Daily generation, original full generation and shared code verification now check whether FFmpeg and the required DejaVu font already exist on the cloud runner. Existing tools are reused. Missing dependencies are installed with bounded three-minute update and install commands instead of an unbounded network fetch. The executable is checked afterward. Rendering stays on GitHub, not the owner's computer. The new code-verification run remains pending until its actual result is read back.

Previously delivered original full proof remains intact; the unsupported solar-coating candidate remains held. No topic, approval or posting decision changed in this dependency fix.
