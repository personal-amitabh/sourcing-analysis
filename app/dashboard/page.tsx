'use client';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useMemo } from 'react';

type Row = {
  Supplier: string;
  Plant: string;
  Item: string;
  'Start Date': string;
  'End Date': string;
  'Sourcing Priority': string | number;
  'Supplier Share %': string | number;
  'Part Description'?: string;
  'Component Type'?: string;
  Material?: string;
  Manufacturer?: string;
  Confidence?: string;
  [key: string]: any;
};

function StatCard({ label, value, sub, color, delay }: any) {
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
}

function Badge({ type }: { type: 'single' | 'multi' }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 500,
      background: type === 'single' ? 'var(--green-dim)' : 'var(--blue-dim)',
      color: type === 'single' ? 'var(--green)' : 'var(--blue)',
      border: `1px solid ${type === 'single' ? 'rgba(34,197,94,0.3)' : 'rgba(59,130,246,0.3)'}`,
      whiteSpace: 'nowrap',
    }}>
      <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'currentColor' }} />
      {type === 'single' ? 'Single' : 'Multi'}
    </span>
  );
}

function ConfidenceBadge({ level }: { level: string }) {
  const map: any = {
    High: { bg: 'var(--green-dim)', color: 'var(--green)', border: 'rgba(34,197,94,0.3)' },
    Medium: { bg: 'var(--accent-dim)', color: 'var(--accent)', border: 'rgba(240,165,0,0.3)' },
    Low: { bg: 'var(--red-dim)', color: 'var(--red)', border: 'rgba(239,68,68,0.3)' },
  };
  const s = map[level] || map.Low;
  return (
    <span style={{
      padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 500,
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
    }}>{level}</span>
  );
}

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [enrichProgress, setEnrichProgress] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);
  const [filterType, setFilterType] = useState<'all' | 'single' | 'multi'>('all');
  const [sortCol, setSortCol] = useState('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 50;

  useEffect(() => {
    if (status === 'unauthenticated') router.push('/login');
  }, [status, router]);

  useEffect(() => {
    if (status === 'authenticated') fetchData();
  }, [status]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sheet');
      const json = await res.json();
      setRows(json.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  // ── Stats ────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    if (!rows.length) return null;

    const uniqueParts = new Set(rows.map(r => r.Item)).size;
    const uniqueSuppliers = new Set(rows.map(r => r.Supplier)).size;

    // Group by Item to determine single vs multi
    const partSuppliers: Record<string, Set<string>> = {};
    rows.forEach(r => {
      if (!partSuppliers[r.Item]) partSuppliers[r.Item] = new Set();
      partSuppliers[r.Item].add(r.Supplier);
    });

    const singleSourced = Object.values(partSuppliers).filter(s => s.size === 1).length;
    const multiSourced = Object.values(partSuppliers).filter(s => s.size > 1).length;

    // Multi-source depth breakdown
    const depthCount: Record<number, number> = {};
    Object.values(partSuppliers).filter(s => s.size > 1).forEach(s => {
      depthCount[s.size] = (depthCount[s.size] || 0) + 1;
    });

    const depthBreakdown = Object.entries(depthCount)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([n, count]) => ({
        suppliers: Number(n),
        count,
        pct: Math.round((count / multiSourced) * 100),
      }));

    const enrichedCount = rows.filter(r => r['Part Description']).length;

    return { uniqueParts, uniqueSuppliers, singleSourced, multiSourced, depthBreakdown, enrichedCount, totalRows: rows.length };
  }, [rows]);

  // ── Filtered + sorted rows ────────────────────────────────────────
  const filtered = useMemo(() => {
    let r = [...rows];
    if (search) {
      const q = search.toLowerCase();
      r = r.filter(row =>
        row.Item?.toLowerCase().includes(q) ||
        row.Supplier?.toLowerCase().includes(q) ||
        row.Plant?.toString().includes(q) ||
        row['Part Description']?.toLowerCase().includes(q)
      );
    }
    if (filterType === 'single') r = r.filter(row => !row['Supplier Share %']);
    if (filterType === 'multi') r = r.filter(row => !!row['Supplier Share %']);
    if (sortCol) {
      r.sort((a, b) => {
        const av = a[sortCol] ?? '', bv = b[sortCol] ?? '';
        return sortDir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
      });
    }
    return r;
  }, [rows, search, filterType, sortCol, sortDir]);

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  const handleSort = (col: string) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('asc'); }
  };

  // ── Enrichment ───────────────────────────────────────────────────
  const handleEnrich = async () => {
    setEnriching(true);
    const unenriched = rows.filter(r => !r['Part Description']);
    setEnrichProgress(`Enriching ${unenriched.length} parts... (processing in batches of 20)`);

    let allUpdates: any[] = [];
    let processed = 0;

    while (processed < unenriched.length) {
      const batch = unenriched.slice(processed, processed + 20);
      try {
        const res = await fetch('/api/enrich', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ parts: batch }),
        });
        const data = await res.json();
        if (data.updates) allUpdates = [...allUpdates, ...data.updates];
        processed += batch.length;
        setEnrichProgress(`Enriched ${Math.min(processed, unenriched.length)} of ${unenriched.length} parts...`);
      } catch (e) {
        console.error('Batch error:', e);
        processed += batch.length;
      }
    }

    // Apply enriched data to rows
    const updatedRows = rows.map(row => {
      const update = allUpdates.find(u => u.Item === row.Item);
      return update ? { ...row, ...update } : row;
    });
    setRows(updatedRows);

    // Write back to sheet
    setEnrichProgress('Writing enriched data back to Google Sheet...');
    const rowUpdates = updatedRows
      .map((row, i) => ({ rowIndex: i + 1, values: row }))
      .filter((_, i) => allUpdates.some(u => u.Item === updatedRows[i].Item));

    const newHeaders = ['Part Description', 'Component Type', 'Material', 'Manufacturer', 'Confidence'];
    await fetch('/api/sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'addColumns', headers: newHeaders, rowUpdates }),
    });

    setEnrichProgress(`✓ Done! Enriched ${allUpdates.length} parts and saved to sheet.`);
    setEnriching(false);
    setTimeout(() => setEnrichProgress(''), 5000);
  };

  if (status === 'loading' || loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '40px', height: '40px', border: '2px solid var(--border)', borderTopColor: 'var(--accent)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>Loading sourcing data...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const COLS = ['Supplier', 'Plant', 'Item', 'Start Date', 'End Date', 'Sourcing Priority', 'Supplier Share %', 'Part Description', 'Component Type', 'Material', 'Manufacturer', 'Confidence'];
  const hasEnrichment = rows.some(r => r['Part Description']);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
        height: '56px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(10,12,16,0.95)',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: '6px',
            background: 'var(--accent-dim)', border: '1px solid var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" stroke="var(--accent)" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '16px', color: 'var(--text-primary)' }}>
            Sourcing Analysis
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{session?.user?.email}</span>
          <button onClick={() => signOut({ callbackUrl: '/login' })} style={{
            padding: '6px 14px', borderRadius: '6px', fontSize: '12px',
            background: 'transparent', border: '1px solid var(--border)',
            color: 'var(--text-secondary)', cursor: 'pointer',
            fontFamily: 'var(--font-body)', transition: 'all 0.2s',
          }}
            onMouseEnter={e => { (e.target as HTMLButtonElement).style.borderColor = 'var(--text-secondary)'; (e.target as HTMLButtonElement).style.color = 'var(--text-primary)'; }}
            onMouseLeave={e => { (e.target as HTMLButtonElement).style.borderColor = 'var(--border)'; (e.target as HTMLButtonElement).style.color = 'var(--text-secondary)'; }}
          >Sign out</button>
        </div>
      </header>

      <main style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto' }}>
        {/* Page title */}
        <div className="fade-up" style={{ marginBottom: '28px' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--text-primary)', marginBottom: '4px' }}>
            Supplier Sourcing Intelligence
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {stats?.totalRows.toLocaleString()} records · Last refreshed just now
          </p>
        </div>

        {/* Stats grid */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '28px' }}>
            <StatCard delay={1} label="Unique Parts" value={stats.uniqueParts.toLocaleString()} sub="distinct item numbers" color="var(--accent)" />
            <StatCard delay={2} label="Unique Suppliers" value={stats.uniqueSuppliers.toLocaleString()} sub="active vendors" color="var(--blue)" />
            <StatCard delay={3} label="Single Sourced" value={stats.singleSourced.toLocaleString()} sub={`${Math.round(stats.singleSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--green)" />
            <StatCard delay={4} label="Multi Sourced" value={stats.multiSourced.toLocaleString()} sub={`${Math.round(stats.multiSourced / stats.uniqueParts * 100)}% of all parts`} color="var(--purple)" />
            {hasEnrichment && (
              <StatCard delay={5} label="AI Enriched" value={stats.enrichedCount.toLocaleString()} sub={`of ${stats.totalRows.toLocaleString()} records`} color="var(--accent)" />
            )}
          </div>
        )}

        {/* Multi-source depth breakdown */}
        {stats && stats.depthBreakdown.length > 0 && (
          <div className="fade-up-5" style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '12px', padding: '20px 24px', marginBottom: '28px',
          }}>
            <div style={{ fontSize: '11px', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Multi-Source Depth Breakdown
            </div>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              {stats.depthBreakdown.map(({ suppliers, count, pct }) => (
                <div key={suppliers} style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '120px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{suppliers} suppliers</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--text-primary)', fontWeight: 500 }}>{pct}%</span>
                  </div>
                  <div style={{ height: '4px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: 'var(--purple)', borderRadius: '2px', transition: 'width 0.6s ease' }} />
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{count.toLocaleString()} parts</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Toolbar */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ position: 'relative', flex: '1', minWidth: '200px', maxWidth: '360px' }}>
            <svg style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} width="14" height="14" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="var(--text-muted)" strokeWidth="2"/>
              <path d="m21 21-4.35-4.35" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <input
              value={searchInput}
              onChange={e => { setSearchInput(e.target.value); setPage(1); }}
              placeholder="Search parts, suppliers..."
              style={{
                width: '100%', padding: '8px 12px 8px 36px',
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: '8px', color: 'var(--text-primary)', fontSize: '13px',
                fontFamily: 'var(--font-body)', outline: 'none',
              }}
              onFocus={e => (e.target.style.borderColor = 'var(--accent)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>

          {/* Filter buttons */}
          {(['all', 'single', 'multi'] as const).map(f => (
            <button key={f} onClick={() => { setFilterType(f); setPage(1); }} style={{
              padding: '7px 16px', borderRadius: '8px', fontSize: '12px', fontWeight: 500,
              border: '1px solid',
              borderColor: filterType === f ? 'var(--accent)' : 'var(--border)',
              background: filterType === f ? 'var(--accent-dim)' : 'transparent',
              color: filterType === f ? 'var(--accent)' : 'var(--text-secondary)',
              cursor: 'pointer', fontFamily: 'var(--font-body)', transition: 'all 0.15s',
              textTransform: 'capitalize',
            }}>
              {f === 'all' ? 'All Parts' : f === 'single' ? 'Single Sourced' : 'Multi Sourced'}
            </button>
          ))}

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
            {enrichProgress && (
              <span style={{ fontSize: '12px', color: enrichProgress.startsWith('✓') ? 'var(--green)' : 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
                {enrichProgress}
              </span>
            )}
            <button onClick={handleEnrich} disabled={enriching} style={{
              padding: '8px 18px', borderRadius: '8px', fontSize: '13px', fontWeight: 500,
              background: enriching ? 'var(--border)' : 'var(--accent)',
              color: enriching ? 'var(--text-muted)' : '#0a0c10',
              border: 'none', cursor: enriching ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-body)', transition: 'all 0.2s',
              display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              {enriching ? (
                <>
                  <div style={{ width: '12px', height: '12px', border: '2px solid rgba(0,0,0,0.3)', borderTopColor: '#000', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                  Enriching...
                </>
              ) : '✦ Enrich Parts'}
            </button>
            <button onClick={fetchData} style={{
              padding: '8px 14px', borderRadius: '8px', fontSize: '12px',
              background: 'transparent', border: '1px solid var(--border)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-body)',
            }}>↻ Refresh</button>
          </div>
        </div>

        {/* Results count */}
        <div style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing {((page - 1) * PAGE_SIZE + 1).toLocaleString()}–{Math.min(page * PAGE_SIZE, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()} rows
        </div>

        {/* Table */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: '12px', overflow: 'hidden',
        }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)' }}>
                  {COLS.map(col => (
                    <th key={col} onClick={() => handleSort(col)} style={{
                      padding: '10px 14px', textAlign: 'left', fontWeight: 500,
                      fontSize: '11px', letterSpacing: '0.06em', textTransform: 'uppercase',
                      color: sortCol === col ? 'var(--accent)' : 'var(--text-secondary)',
                      cursor: 'pointer', whiteSpace: 'nowrap',
                      userSelect: 'none',
                    }}>
                      {col} {sortCol === col ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginated.map((row, i) => {
                  const isMulti = !!row['Supplier Share %'];
                  return (
                    <tr key={i} style={{
                      borderBottom: '1px solid var(--border)',
                      transition: 'background 0.1s',
                    }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', whiteSpace: 'nowrap', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.Supplier}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{row.Plant}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--accent)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>{row.Item}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{row['Start Date']}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{row['End Date']}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', textAlign: 'center' }}>{row['Sourcing Priority']}</td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Badge type={isMulti ? 'multi' : 'single'} />
                          {isMulti && <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: '11px' }}>{row['Supplier Share %']}%</span>}
                        </div>
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-primary)', maxWidth: '180px' }}>{row['Part Description'] || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{row['Component Type'] || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>{row.Material || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{row.Manufacturer || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                      <td style={{ padding: '10px 14px' }}>
                        {row.Confidence ? <ConfidenceBadge level={row.Confidence} /> : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{
              padding: '12px 16px', borderTop: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Page {page} of {totalPages}
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={{
                  padding: '6px 14px', borderRadius: '6px', fontSize: '12px',
                  background: 'transparent', border: '1px solid var(--border)',
                  color: page === 1 ? 'var(--text-muted)' : 'var(--text-secondary)',
                  cursor: page === 1 ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-body)',
                }}>← Prev</button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={{
                  padding: '6px 14px', borderRadius: '6px', fontSize: '12px',
                  background: 'transparent', border: '1px solid var(--border)',
                  color: page === totalPages ? 'var(--text-muted)' : 'var(--text-secondary)',
                  cursor: page === totalPages ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-body)',
                }}>Next →</button>
              </div>
            </div>
          )}
        </div>
      </main>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
