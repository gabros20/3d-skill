/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// The 4.0.536 headless shell (Chromium 157) aborts on macOS 26 ("icudtl.dat not found in bundle",
// GPU process exits → "Target closed"). Chrome for Testing renders the same frames; drop this
// once a later headless shell launches here.
Config.setChromeMode("chrome-for-testing");
Config.overrideWebpackConfig(enableTailwind);
