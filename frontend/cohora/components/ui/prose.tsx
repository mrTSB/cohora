export function TypographyH1(props: { children: React.ReactNode }) {
  const { children } = props;
  return (
    <h1 className="scroll-m-20 text-4xl mt-6 mb-4 font-extrabold tracking-tight lg:text-5xl">
      {children}
    </h1>
  );
}

export function TypographyH2(props: { children: React.ReactNode }) {
  const { children } = props;
  return (
    <h2 className="scroll-m-20 border-b pb-2 text-3xl mt-6 font-semibold tracking-tight first:mt-0">
      {children}
    </h2>
  );
}

export function TypographyH3(props: { children: React.ReactNode }) {
  const { children } = props;
  return (
    <h3 className="scroll-m-20 text-2xl mt-6 mb-4 font-semibold tracking-tight">{children}</h3>
  );
}
export function TypographyH4(props: { children: React.ReactNode }) {
  const { children } = props;
  return <h4 className="scroll-m-20 text-xl mt-6 mb-4 font-semibold tracking-tight">{children}</h4>;
}

export function TypographyP(props: { children: React.ReactNode }) {
  const { children } = props;
  return <p className="leading-7 [&:not(:first-child)]:mt-6">{children}</p>;
}

export function TypographyBlockquote(props: { children: React.ReactNode }) {
  const { children } = props;
  return <blockquote className="mt-6 border-l-2 pl-6 italic">{children}</blockquote>;
}
