const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');
const path = require('path');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Support @/ path aliases (mirrors tsconfig.json paths)
const projectRoot = __dirname;
config.resolver = config.resolver || {};

// Custom resolver for @/ prefix - delegates back to Metro after translating path
const originalResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (moduleName.startsWith('@/')) {
    const translated = moduleName.replace(/^@\//, './');
    // Use the standard resolution with translated path from project root
    return context.resolveRequest(
      { ...context, originModulePath: path.join(projectRoot, 'index.js') },
      translated,
      platform
    );
  }
  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = withNativeWind(config, { input: './global.css' });
