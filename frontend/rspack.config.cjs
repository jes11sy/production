const path = require('path');

const isProduction = process.env.NODE_ENV === 'production';

/**
 * @type {import('@rspack/cli').Configuration}
 */
module.exports = {
  entry: './src/main.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isProduction ? '[name].[contenthash:8].js' : '[name].js',
    chunkFilename: isProduction ? '[name].[contenthash:8].chunk.js' : '[name].chunk.js',
    assetModuleFilename: isProduction ? 'assets/[name].[contenthash:8][ext]' : 'assets/[name][ext]',
    clean: true,
    publicPath: '/'
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx']
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: 'builtin:swc-loader',
            options: {
              jsc: {
                parser: {
                  syntax: 'typescript',
                  tsx: true
                },
                transform: {
                  react: {
                    runtime: 'automatic'
                  }
                }
              }
            }
          }
        ],
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader',
          'postcss-loader'
        ]
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
        generator: {
          filename: isProduction ? 'images/[name].[contenthash:8][ext]' : 'images/[name][ext]'
        }
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: isProduction ? 'fonts/[name].[contenthash:8][ext]' : 'fonts/[name][ext]'
        }
      }
    ]
  },
  plugins: [
    new (require('@rspack/core').HtmlRspackPlugin)({
      template: './index.html',
      filename: 'index.html',
      minify: isProduction
    }),
    new (require('@rspack/core').DefinePlugin)({
      'process.env.API_URL': JSON.stringify(process.env.API_URL || '/api/v1'),
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
    })
  ],
  mode: isProduction ? 'production' : 'development',
  optimization: {
    minimize: isProduction,
    splitChunks: {
      chunks: 'all',
      minSize: 20000,
      maxSize: 244000,
      cacheGroups: {
        default: {
          minChunks: 2,
          priority: -20,
          reuseExistingChunk: true
        },
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: -10,
          chunks: 'all'
        },
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react',
          priority: 10,
          chunks: 'all'
        },
        ui: {
          test: /[\\/]node_modules[\\/](@heroui|@heroicons)[\\/]/,
          name: 'ui',
          priority: 10,
          chunks: 'all'
        }
      }
    },
    usedExports: true,
    sideEffects: false
  },
  performance: isProduction ? {
    maxAssetSize: 512000,
    maxEntrypointSize: 512000,
    hints: 'warning'
  } : false,
  devtool: isProduction ? 'source-map' : 'cheap-module-source-map',
  devServer: !isProduction ? {
    port: 3000,
    historyApiFallback: true,
    hot: true,
    compress: true,
    proxy: [
      {
        context: ['/api'],
        target: process.env.NODE_ENV === 'production' ? 'https://lead-schem.ru' : 'http://localhost:8000',
        changeOrigin: true,
        secure: process.env.NODE_ENV === 'production',
        cookieDomainRewrite: process.env.NODE_ENV === 'production' ? 'lead-schem.ru' : 'localhost',
        cookiePathRewrite: '/',
        onProxyReq: (proxyReq, req, res) => {
          // Передаем cookies
          if (req.headers.cookie) {
            proxyReq.setHeader('cookie', req.headers.cookie);
          }
        },
        onProxyRes: (proxyRes, req, res) => {
          // Обрабатываем Set-Cookie заголовки
          if (proxyRes.headers['set-cookie']) {
            proxyRes.headers['set-cookie'] = proxyRes.headers['set-cookie'].map(cookie => {
              return cookie.replace(/Domain=[^;]+;?\s*/i, '').replace(/Secure;?\s*/i, '');
            });
          }
        }
      }
    ]
  } : undefined
}; 