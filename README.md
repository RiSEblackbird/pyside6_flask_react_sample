# プロジェクトのディレクトリで以下のコマンドを実行
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
mkdir src/types
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p



tailwind.config.js を上書き
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

src/index.css を上書き
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';