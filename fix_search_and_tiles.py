dashboard = open('app/dashboard/page.tsx', 'r').read()

# Fix 1: Make search debounced (400ms delay, no crash)
old = """  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);"""

new = """  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => { setSearch(searchInput); setPage(1); }, 500);
    return () => clearTimeout(timer);
  }, [searchInput]);"""

dashboard = dashboard.replace(old, new)

# Fix 2: Add activeFilter state for tile drill-down
old = "  const [filterType, setFilterType] = useState<'all' | 'single' | 'multi'>('all');"
new = """  const [filterType, setFilterType] = useState<'all' | 'single' | 'multi'>('all');
  const [tileFilter, setTileFilter] = useState<'all' | 'single' | 'multi' | 'enriched'>('all');"""
dashboard = dashboard.replace(old, new)

# Fix 3: Update filtered rows to respect tileFilter
old = """  // Data comes paginated from server
  const filtered = rows;
  const paginated = rows;"""

new = """  // Filter rows based on search + filterType + tileFilter
  const filtered = useMemo(() => {
    let r = [...rows];

    // Apply tile filter
    if (tileFilter === 'single') {
      const partSuppliers: Record<string, Set<string>> = {};
      rows.forEach((row: Row) => {
        const item = String(row.Item || '').trim();
        const supplier = String(row.Supplier || '').trim();
        if (!partSuppliers[item]) partSuppliers[item] = new Set();
        if (supplier) partSuppliers[item].add(supplier);
      });
      r = r.filter((row: Row) => (partSuppliers[String(row.Item).trim()]?.size || 0) === 1);
    } else if (tileFilter === 'multi') {
      const partSuppliers: Record<string, Set<string>> = {};
      rows.forEach((row: Row) => {
        const item = String(row.Item || '').trim();
        const supplier = String(row.Supplier || '').trim();
        if (!partSuppliers[item]) partSuppliers[item] = new Set();
        if (supplier) partSuppliers[item].add(supplier);
      });
      r = r.filter((row: Row) => (partSuppliers[String(row.Item).trim()]?.size || 0) > 1);
    } else if (tileFilter === 'enriched') {
      r = r.filter((row: Row) => !!row['Part Description']);
    }

    // Apply sourcing type filter buttons
    if (filterType === 'single') r = r.filter((row: Row) => {
      const partSuppliers: Record<string, Set<string>> = {};
      rows.forEach((x: Row) => {
        const item = String(x.Item || '').trim();
        if (!partSuppliers[item]) partSuppliers[item] = new Set();
        if (x.Supplier) partSuppliers[item].add(x.Supplier);
      });
      return (partSuppliers[String(row.Item).trim()]?.size || 0) === 1;
    });
    if (filterType === 'multi') r = r.filter((row: Row) => {
      const partSuppliers: Record<string, Set<string>> = {};
      rows.forEach((x: Row) => {
        const item = String(x.Item || '').trim();
        if (!partSuppliers[item]) partSuppliers[item] = new Set();
        if (x.Supplier) partSuppliers[item].add(x.Supplier);
      });
      return (partSuppliers[String(row.Item).trim()]?.size || 0) > 1;
    });

    // Apply search
    if (search) {
      const q = search.toLowerCase();
      r = r.filter((row: Row) =>
        String(row.Item || '').toLowerCase().includes(q) ||
        String(row.Supplier || '').toLowerCase().includes(q) ||
        String(row.Plant || '').toLowerCase().includes(q) ||
        String(row['Part Description'] || '').toLowerCase().includes(q)
      );
    }

    return r;
  }, [rows, search, filterType, tileFilter]);

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);"""

dashboard = dashboard.replace(old, new)

# Fix 4: Update totalRows and totalPages to use filtered
old = """        <div style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing {((page - 1) * PAGE_SIZE + 1).toLocaleString()}–{Math.min(page * PAGE_SIZE, totalRows).toLocaleString()} of {totalRows.toLocaleString()} rows
        </div>"""
new = """        <div style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
          {tileFilter !== 'all' && (
            <span style={{ marginRight: '8px', color: 'var(--accent)', fontWeight: 500 }}>
              Filtered by: {tileFilter === 'single' ? 'Single Sourced' : tileFilter === 'multi' ? 'Multi Sourced' : 'AI Enriched'}
              <button onClick={() => { setTileFilter('all'); setPage(1); }} style={{ marginLeft: '6px', background: 'none', border: 'none', color: 'var(--red)', cursor: 'pointer', fontSize: '12px' }}>✕ Clear</button>
            </span>
          )}
          Showing {Math.min((page - 1) * PAGE_SIZE + 1, filtered.length).toLocaleString()}–{Math.min(page * PAGE_SIZE, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()} rows
        </div>"""
dashboard = dashboard.replace(old, new)

# Fix 5: Update pagination to use filtered.length
old = """  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);"""
new = """  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  // totalPages already computed above"""
dashboard = dashboard.replace(old, new)

# Fix 6: Make stat cards clickable - update StatCard to accept onClick
old = """function StatCard({ label, value, sub, color, delay }: any) {
  return (
    <div className={`fade-up-${delay}`} style={{
      background: 'var(--bg-card)',
      border: `1px solid var(--border)`,
      borderRadius: '12px',
      padding: '20px 24px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.2s, background 0.2s',
    }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = color;
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card-hover)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)';
        (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card)';
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: color, opacity: 0.6,
      }} />
      <div style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ fontSize: '32px', fontFamily: 'var(--font-mono)', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '6px' }}>{sub}</div>}
    </div>
  );
}"""

new = """function StatCard({ label, value, sub, color, delay, onClick, active }: any) {
  return (
    <div className={`fade-up-${delay}`} onClick={onClick} style={{
      background: active ? `rgba(${color === 'var(--accent)' ? '196,127,0' : color === 'var(--green)' ? '22,163,74' : color === 'var(--blue)' ? '37,99,235' : color === 'var(--purple)' ? '124,58,237' : '196,127,0'}, 0.08)` : 'var(--bg-card)',
      border: `1px solid ${active ? color : 'var(--border)'}`,
      borderRadius: '12px',
      padding: '20px 24px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.2s, background 0.2s, transform 0.1s',
      cursor: onClick ? 'pointer' : 'default',
      transform: active ? 'translateY(-2px)' : 'none',
      boxShadow: active ? `0 4px 12px rgba(0,0,0,0.08)` : 'none',
    }}
      onMouseEnter={e => {
        if (onClick) {
          (e.currentTarget as HTMLDivElement).style.borderColor = color;
          (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card-hover)';
        }
      }}
      onMouseLeave={e => {
        if (onClick && !active) {
          (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)';
          (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card)';
        }
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
        background: color, opacity: active ? 1 : 0.6,
      }} />
      <div style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '8px' }}>
        {label} {onClick && <span style={{ fontSize: '10px', opacity: 0.6 }}>↓</span>}
      </div>
      <div style={{ fontSize: '32px', fontFamily: 'var(--font-mono)', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '6px' }}>{sub}</div>}
    </div>
  );
}"""

dashboard = dashboard.replace(old, new)

# Fix 7: Update StatCard usages to add onClick and active props
old = """            <StatCard delay={1} label="Unique Parts" value={stats.uniqueParts.toLocaleString()} sub="distinct item numbers" color="var(--accent)" />
            <StatCard delay={2} label="Unique Suppliers" value={stats.uniqueSuppliers.toLocaleString()} sub="active vendors" color="var(--blue)" />
            <StatCard delay={3} label="Single Sourced" value={stats.singleSourced.toLocaleString()} sub={`${Math.round(stats.singleSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--green)" />
            <StatCard delay={4} label="Multi Sourced" value={stats.multiSourced.toLocaleString()} sub={`${Math.round(stats.multiSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--purple)" />
            {hasEnrichment && (
              <StatCard delay={5} label="AI Enriched" value={stats.enrichedCount.toLocaleString()} sub={`of ${stats.totalRows.toLocaleString()} records`} color="var(--accent)" />
            )}"""

new = """            <StatCard delay={1} label="Unique Parts" value={stats.uniqueParts.toLocaleString()} sub="distinct item numbers" color="var(--accent)" />
            <StatCard delay={2} label="Unique Suppliers" value={stats.uniqueSuppliers.toLocaleString()} sub="active vendors" color="var(--blue)" />
            <StatCard delay={3} label="Single Sourced" value={stats.singleSourced.toLocaleString()} sub={`${Math.round(stats.singleSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--green)" onClick={() => { setTileFilter(tileFilter === 'single' ? 'all' : 'single'); setPage(1); }} active={tileFilter === 'single'} />
            <StatCard delay={4} label="Multi Sourced" value={stats.multiSourced.toLocaleString()} sub={`${Math.round(stats.multiSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--purple)" onClick={() => { setTileFilter(tileFilter === 'multi' ? 'all' : 'multi'); setPage(1); }} active={tileFilter === 'multi'} />
            {hasEnrichment && (
              <StatCard delay={5} label="AI Enriched" value={stats.enrichedCount.toLocaleString()} sub={`of ${stats.totalRows.toLocaleString()} records`} color="var(--accent)" onClick={() => { setTileFilter(tileFilter === 'enriched' ? 'all' : 'enriched'); setPage(1); }} active={tileFilter === 'enriched'} />
            )}"""

dashboard = dashboard.replace(old, new)

open('app/dashboard/page.tsx', 'w').write(dashboard)
print("✅ Done!")
