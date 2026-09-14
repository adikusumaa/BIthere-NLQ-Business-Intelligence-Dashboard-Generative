/**
 * Minimal markdown renderer: bold, italic, inline code, links.
 * Avoids external dependencies.
 */

function renderInline(text) {
  const nodes = [];
  const regex =
    /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      nodes.push(
        <code
          key={key++}
          style={{
            background: "var(--color-bg)",
            padding: "1px 5px",
            borderRadius: "4px",
            fontSize: "12px",
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("*")) {
      nodes.push(<em key={key++}>{token.slice(1, -1)}</em>);
    } else if (token.startsWith("[")) {
      const label = token.slice(1, token.indexOf("]"));
      const url = token.slice(token.indexOf("(") + 1, -1);
      nodes.push(
        <a key={key++} href={url} target="_blank" rel="noreferrer">
          {label}
        </a>
      );
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

export default function MarkdownLite({ text }) {
  if (!text) return null;
  return <>{renderInline(text)}</>;
}