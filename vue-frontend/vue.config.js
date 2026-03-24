const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: '../static',
  parallel: false, // Отключаем параллельную обработку для избежания проблем с thread-loader на Windows
  chainWebpack(config) {
    config.resolve.extensions.add('.ts')
    config.module
      .rule('ts')
      .test(/\.ts$/)
      .exclude.add(/node_modules/)
      .end()
      .use('ts-loader')
      .loader('ts-loader')
      .options({ transpileOnly: true })
  },
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/register': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/login': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/user_profile': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
