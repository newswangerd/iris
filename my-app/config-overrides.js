const { override, addWebpackPlugin } = require("customize-cra");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = override(
  addWebpackPlugin(
    new CopyPlugin({
      // Use copy plugin to copy *.wasm to output folder.
      patterns: [
        {
          from: "node_modules/onnxruntime-web/dist/*.wasm",
          to: "static/js/[name][ext]",
        },
        {
          from: "node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js",
          to: "static/js/",
        },
        {
          from: "node_modules/@ricky0123/vad-web/dist/*.onnx",
          to: "static/js/[name][ext]",
        },
        {
          from: "node_modules/onnxruntime-web/dist/*.wasm",
          to: "static/js/[name][ext]",
        },
        {
          from: "node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.mjs",
          to: "static/js/",
        },
        {
          from: "node_modules/opus-recorder/dist/encoderWorker.min.js",
          to: "",
        },
      ],
    }),
  ),
);
