"use strict";
// Read project instructions at each compaction; no token/model changes.
const fs = require("node:fs");
const path = require("node:path");

function withProjectInstructions(runtime, explicit) {
  if (typeof runtime?.workingDirectory !== "string") return explicit;
  let directory = path.resolve(runtime.workingDirectory);
  for (let depth = 0; depth < 16; depth += 1) {
    const file = path.join(directory, ".zcode", "COMPACT_INSTRUCTIONS.md");
    try {
      if (fs.statSync(file).size > 16384) {
        runtime.logger?.warn("Project compact instructions exceed 16 KiB; using explicit instructions", {file});
        return explicit;
      }
      const instructions = fs.readFileSync(file, "utf8").trim();
      if (instructions) {
        return [instructions, explicit].filter(value => typeof value === "string" && value.trim()).join("\n\n");
      }
      return explicit;
    } catch (error) {
      if (error.code !== "ENOENT" && error.code !== "ENOTDIR") {
        runtime.logger?.warn("Cannot read project compact instructions; using explicit instructions",
                              {file, error: String(error)});
        return explicit;
      }
    }
    const parent = path.dirname(directory);
    if (parent === directory) break;
    directory = parent;
  }
  return explicit;
}
module.exports = {withProjectInstructions};
