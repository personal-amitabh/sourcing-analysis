dashboard = open('app/dashboard/page.tsx', 'r').read()

# Restore stats computation from rows
old = "  // Stats now come from server"
new = """  // Compute stats from loaded rows
  const stats = useMemo(() => {
    if (!rows.length) return null;

    const uniqueParts = new Set(rows.map((r: Row) => r.Item)).size;
    const uniqueSuppliers = new Set(rows.map((r: Row) => r.Supplier)).size;

    const partSuppliers: Record<string, Set<string>> = {};
    rows.forEach((r: Row) => {
      if (!partSuppliers[r.Item]) partSuppliers[r.Item] = new Set();
      partSuppliers[r.Item].add(r.Supplier);
    });

    const singleSourced = Object.values(partSuppliers).filter(s => s.size === 1).length;
    const multiSourced = Object.values(partSuppliers).filter(s => s.size > 1).length;

    const depthCount: Record<number, number> = {};
    Object.values(partSuppliers).filter(s => s.size > 1).forEach(s => {
      depthCount[s.size] = (depthCount[s.size] || 0) + 1;
    });

    const depthBreakdown = Object.entries(depthCount)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([n, count]) => ({
        suppliers: Number(n),
        count: Number(count),
        pct: Math.round((Number(count) / multiSourced) * 100),
      }));

    const enrichedCount = rows.filter((r: Row) => r['Part Description']).length;

    return { uniqueParts, uniqueSuppliers, singleSourced, multiSourced, depthBreakdown, enrichedCount, totalRows: rows.length };
  }, [rows]);"""

dashboard = dashboard.replace(old, new)

# Remove extra stats state since we're using useMemo now
old2 = "  const [stats, setStats] = useState<any>(null);"
new2 = ""
dashboard = dashboard.replace(old2, new2)

open('app/dashboard/page.tsx', 'w').write(dashboard)
print("✅ Done!")
