const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';
const publicPath = isProduction ? '/wxb5/' : '/';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  entry: './src/js/index.js',
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isProduction ? 'js/[name].[contenthash:8].js' : 'js/[name].js',
    clean: {
      keep: /\.json$/,
    },
    publicPath: publicPath
  },
  
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      {
        test: /\.css$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          'css-loader'
        ]
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg|webp)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'images/[name].[hash:8][ext]'
        }
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[hash:8][ext]'
        }
      }
    ]
  },
  
  plugins: [
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'node_modules/chart.js/dist/chart.umd.js',
          to: 'js/chart.umd.js'
        },
        {
          from: 'data',
          to: 'data',
          noErrorOnMissing: true
        }
      ]
    }),
    new HtmlWebpackPlugin({
      template: './index.html',
      filename: 'index.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './football.html',
      filename: 'football.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './basketball.html',
      filename: 'basketball.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './bjdc.html',
      filename: 'bjdc.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './sggg.html',
      filename: 'sggg.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './ctzc.html',
      filename: 'ctzc.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './rx9.html',
      filename: 'rx9.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './bqc6.html',
      filename: 'bqc6.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './zjq4.html',
      filename: 'zjq4.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './dlt.html',
      filename: 'dlt.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './dlt_chart.html',
      filename: 'dlt_chart.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './qxc.html',
      filename: 'qxc.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './qxc_chart.html',
      filename: 'qxc_chart.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './pls.html',
      filename: 'pls.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './pls_chart.html',
      filename: 'pls_chart.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './plw.html',
      filename: 'plw.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './plw_chart.html',
      filename: 'plw_chart.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './match_analysis.html',
      filename: 'match_analysis.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './basketball_analysis.html',
      filename: 'basketball_analysis.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './data_monitor.html',
      filename: 'data_monitor.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './live.html',
      filename: 'live.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './live_detail.html',
      filename: 'live_detail.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new HtmlWebpackPlugin({
      template: './database.html',
      filename: 'database.html',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
      } : false
    }),
    new MiniCssExtractPlugin({
      filename: isProduction ? 'css/[name].[contenthash:8].css' : 'css/[name].css'
    })
  ],
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin(),
      new CssMinimizerPlugin()
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  },
  
  devServer: {
    static: [
      {
        directory: path.join(__dirname, 'dist'),
        publicPath: '/'
      }
    ],
    compress: true,
    port: 8082,
    hot: true,
    open: true,
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws'
    },
    historyApiFallback: {
      disableDotRule: true
    },
    proxy: {
      '/api': {
        target: 'https://webapi.sporttery.cn',
        changeOrigin: true,
        secure: false,
        pathRewrite: { '^/api': '' }
      },
      '/500api': {
        target: 'https://trade.500.com',
        changeOrigin: true,
        secure: false,
        pathRewrite: { '^/500api': '' }
      }
    }
  },
  
  resolve: {
    extensions: ['.js'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@js': path.resolve(__dirname, 'src/js'),
      '@css': path.resolve(__dirname, 'src/css'),
      '@images': path.resolve(__dirname, 'src/images')
    }
  },
  
  devtool: isProduction ? 'source-map' : 'eval-source-map'
};