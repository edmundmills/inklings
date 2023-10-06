const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const path = require('path');

module.exports = {
    entry: './app/static/scss/bootstrap_overrides.scss',
    module: {
        rules: [
            {
                test: /\.scss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader'
                ]
            }
        ]
    },
    output: {
        path: path.resolve(__dirname, 'app/static'),
        filename: 'js/bundled.js'  // if you also have JS
    },    
    plugins: [
        new MiniCssExtractPlugin({
            filename: 'css/bootstrap.css'
        })
    ]
};


