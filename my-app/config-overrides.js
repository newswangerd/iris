const { override, addWebpackPlugin } = require("customize-cra");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = override(
  addWebpackPlugin(
    new CopyPlugin({
      // Use copy plugin to copy *.wasm to output folder.
      patterns: [
        {
          from: "node_modules/opus-recorder/dist/encoderWorker.min.js",
          to: "",
        },
      ],
    }),
  ),
);
