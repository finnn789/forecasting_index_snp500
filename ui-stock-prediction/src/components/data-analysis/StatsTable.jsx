import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'

function formatValue(value) {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(4)
  }
  return String(value)
}

export default function StatsTable({ data }) {
  const columnNames = Object.keys(data.columns)
  const statNames = Object.keys(data.columns[columnNames[0]] ?? {})

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Stat</TableHead>
          {columnNames.map((col) => (
            <TableHead key={col}>{col}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {statNames.map((stat) => (
          <TableRow key={stat}>
            <TableCell className="font-medium text-slate-500">{stat}</TableCell>
            {columnNames.map((col) => (
              <TableCell key={col} className="font-mono">
                {formatValue(data.columns[col][stat])}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
