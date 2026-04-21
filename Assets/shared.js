(function(global) {
  async function loadJson(path) {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Failed to load JSON at ${path}: ${response.status}`);
    }
    return response.json();
  }

  global.DanBeemData = {
    loadJson
  };
})(window);
