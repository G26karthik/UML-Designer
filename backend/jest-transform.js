export default {
  process(src, filename) {
    // Replace import.meta.url with a mock URL for tests
    return src.replace(/import\.meta\.url/g, "'file://" + filename + "'");
  },
};