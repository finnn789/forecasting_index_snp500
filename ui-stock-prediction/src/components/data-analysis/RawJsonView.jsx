export default function RawJsonView({ data }) {
  return (
    <pre className="max-h-120 overflow-auto rounded-lg bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-200">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}
