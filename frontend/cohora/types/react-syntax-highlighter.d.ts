declare module 'react-syntax-highlighter/dist/esm/styles/hljs' {
  export const solarizedDark: any;
}

declare module 'react-syntax-highlighter' {
  import { ComponentType } from 'react';
  
  interface SyntaxHighlighterProps {
    language?: string;
    style?: any;
    children: string;
    PreTag?: string | ComponentType;
    className?: string;
  }
  
  export const Prism: ComponentType<SyntaxHighlighterProps>;
} 