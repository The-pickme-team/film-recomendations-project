import pluginJs from "@eslint/js";
import pluginReact from "eslint-plugin-react";
import pluginReactHooks from "eslint-plugin-react-hooks";
import globals from "globals";

export default [
  {
    ignores: [
      "dist/**", 
      "build/**", 
      "node_modules/**", 
      ".venv/**"
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs,jsx}"],
    
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    
    plugins: {
      javascript: pluginJs,
      react: pluginReact,
      "react-hooks": pluginReactHooks,
    },
    
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
      "no-const-assign": "error",
      
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react/react-in-jsx-scope": "off",
    },
    
    settings: {
      react: {
        version: "detect",
      },
    },
  },
];