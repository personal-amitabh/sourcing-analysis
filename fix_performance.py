import re

# ── Fix 1: Update Apps Script to support pagination + search ──────
apps_script = """const SHEET_NAME = 'Sourcing';
const SECRET_TOKEN = '50ea2e9d367615cd294b5b2162d102dc3da8e5c61c7546879aa018e852559d8d'; // keep your existing token

function doGet(e) {
  if (e.parameter.token !== SECRET_TOKEN) {
    return jsonResponse({ error: 'Unauthorized' });
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  const search = (e.parameter.search || '').toLowerCase();
  const filter = e.parameter.filter || 'all';
  const page = parseInt(e.parameter.page || '1');
  const pageSize = parseInt(e.parameter.pageSize || '500');

  let rows = data.slice(1).map(row => {
    const obj = {};
    headers.forEach((h, i) => obj[h] = row[i]);
    return obj;
  });

  // Apply search filter server-side
  if (search) {
    rows = rows.filter(row =>
      String(row['Supplier'] || '').toLowerCase().includes(search) ||
      String(row['Item'] || '').toLowerCase().includes(search) ||
      String(row['Plant'] || '').toLowerCase().includes(search) ||
      String(row['Part Description'] || '').toLowerCase().includes(search)
    );
  }

  // Apply sourcing type filter
  if (filter === 'single') rows = rows.filter(r => !r['Supplier Share %']);
  if (filter === 'multi') rows = rows.filter(r => !!r['Supplier Share %']);

  const total = rows.length;
  const start = (page - 1) * pageSize;
  const paged = rows.slice(start, start + pageSize);

  // Compute stats from ALL rows (not paged)
  const allRows = data.slice(1).map(row => {
    const obj = {};
    headers.forEach((h, i) => obj[h] = row[i]);
    return obj;
  });

  const uniqueParts = new Set(allRows.map(r => r['Item'])).size;
  const uniqueSuppliers = new Set(allRows.map(r => r['Supplier'])).size;

  const partSuppliers = {};
  allRows.forEach(r => {
    if (!partSuppliers[r['Item']]) partSuppliers[r['Item']] = new Set();
    partSuppliers[r['Item']].add(r['Supplier']);
  });

  const singleSourced = Object.values(partSuppliers).filter(s => s.size === 1).length;
  const multiSourced = Object.values(partSuppliers).filter(s => s.size > 1).length;

  const depthCount = {};
  Object.values(partSuppliers).filter(s => s.size > 1).forEach(s => {
    depthCount[s.size] = (depthCount[s.size] || 0) + 1;
  });

  const depthBreakdown = Object.entries(depthCount)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([n, count]) => ({
      suppliers: Number(n),
      count: count,
      pct: Math.round((count / multiSourced) * 100)
    }));

  return jsonResponse({
    data: paged,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
    stats: { uniqueParts, uniqueSuppliers, singleSourced, multiSourced, depthBreakdown, totalRows: allRows.length }
  });
}

function doPost(e) {
  const body = JSON.parse(e.postData.contents);
  if (body.token !== SECRET_TOKEN) {
    return jsonResponse({ error: 'Unauthorized' });
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);

  if (body.action === 'addColumns') {
    const { headers, rowUpdates } = body;
    const existingHeaders = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

    headers.forEach(h => {
      if (!existingHeaders.includes(h)) {
        const newCol = sheet.getLastColumn() + 1;
        sheet.getRange(1, newCol).setValue(h);
        existingHeaders.push(h);
      }
    });

    rowUpdates.forEach(({ rowIndex, values }) => {
      headers.forEach(h => {
        const colIndex = existingHeaders.indexOf(h) + 1;
        sheet.getRange(rowIndex + 1, colIndex).setValue(values[h] || '');
      });
    });

    return jsonResponse({ success: true });
  }

  return jsonResponse({ error: 'Unknown action' });
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}"""

print("\\n📋 APPS SCRIPT CODE:")
print("="*60)
print(apps_script)
print("="*60)
print("\\n👆 Copy the above code into your Apps Script editor and redeploy.\\n")

# ── Fix 2: Update the sheet API route ────────────────────────────
sheet_route = """import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';

const APPS_SCRIPT_URL = process.env.NEXT_PUBLIC_APPS_SCRIPT_URL!;
const TOKEN = process.env.APPS_SCRIPT_TOKEN!;

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { searchParams } = new URL(req.url);
  const search = searchParams.get('search') || '';
  const filter = searchParams.get('filter') || 'all';
  const page = searchParams.get('page') || '1';

  try {
    const url = `${APPS_SCRIPT_URL}?token=${TOKEN}&search=${encodeURIComponent(search)}&filter=${filter}&page=${page}&pageSize=500`;
    const res = await fetch(url);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ error: 'Failed to fetch sheet data' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const body = await req.json();
    const res = await fetch(APPS_SCRIPT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, token: TOKEN }),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ error: 'Failed to update sheet' }, { status: 500 });
  }
}
"""

with open('app/api/sheet/route.ts', 'w') as f:
    f.write(sheet_route)
print("✅ Updated app/api/sheet/route.ts")

# ── Fix 3: Update dashboard to use server-side search ────────────
dashboard = open('app/dashboard/page.tsx', 'r').read()

# Replace fetchData function
old_fetch = """  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/sheet');
      const json = await res.json();
      setRows(json.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };"""

new_fetch = """  const fetchData = async (searchVal = search, filterVal = filterType, pageVal = page) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ search: searchVal, filter: filterVal, page: String(pageVal) });
      const res = await fetch(`/api/sheet?${params}`);
      const json = await res.json();
      setRows(json.data || []);
      setTotalRows(json.total || 0);
      setTotalPages(json.totalPages || 1);
      if (json.stats) setStats(json.stats);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };"""

dashboard = dashboard.replace(old_fetch, new_fetch)

# Replace stats useState and add new state variables
old_states = "  const [page, setPage] = useState(1);\n  const PAGE_SIZE = 50;"
new_states = """  const [page, setPage] = useState(1);
  const PAGE_SIZE = 500;
  const [totalRows, setTotalRows] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState<any>(null);"""

dashboard = dashboard.replace(old_states, new_states)

# Remove the useMemo stats computation (now comes from server)
old_stats_memo = """  // ── Stats ────────────────────────────────────────────────────────
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
  }, [rows]);"""

new_stats_memo = """  // Stats now come from server"""

dashboard = dashboard.replace(old_stats_memo, new_stats_memo)

# Replace filtered/paginated logic (now handled server-side)
old_filtered = """  // ── Filtered + sorted rows ────────────────────────────────────────
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
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);"""

new_filtered = """  // Data comes paginated from server
  const filtered = rows;
  const paginated = rows;"""

dashboard = dashboard.replace(old_filtered, new_filtered)

# Update search input to trigger server fetch on Enter key
old_search_input = """onChange={e => { setSearchInput(e.target.value); setPage(1); }}"""
new_search_input = """onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { setPage(1); fetchData(searchInput, filterType, 1); } }}"""
dashboard = dashboard.replace(old_search_input, new_search_input)

# Update filter buttons to trigger server fetch
old_filter_btn = """onClick={() => { setFilterType(f); setPage(1); }}"""
new_filter_btn = """onClick={() => { setFilterType(f); setPage(1); fetchData(search, f, 1); }}"""
dashboard = dashboard.replace(old_filter_btn, new_filter_btn)

# Update showing count to use totalRows
old_showing = """Showing {((page - 1) * PAGE_SIZE + 1).toLocaleString()}–{Math.min(page * PAGE_SIZE, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()} rows"""
new_showing = """Showing {((page - 1) * PAGE_SIZE + 1).toLocaleString()}–{Math.min(page * PAGE_SIZE, totalRows).toLocaleString()} of {totalRows.toLocaleString()} rows"""
dashboard = dashboard.replace(old_showing, new_showing)

# Update pagination buttons
old_prev = """onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}"""
new_prev = """onClick={() => { const p = Math.max(1, page - 1); setPage(p); fetchData(search, filterType, p); }} disabled={page === 1}"""
dashboard = dashboard.replace(old_prev, new_prev)

old_next = """onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}"""
new_next = """onClick={() => { const p = Math.min(totalPages, page + 1); setPage(p); fetchData(search, filterType, p); }} disabled={page === totalPages}"""
dashboard = dashboard.replace(old_next, new_next)

# Add search button next to search input
old_input_end = """onFocus={e => (e.target.style.borderColor = 'var(--accent)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>"""
new_input_end = """onFocus={e => (e.target.style.borderColor = 'var(--accent)')}
              onBlur={e => (e.target.style.borderColor = 'var(--border)')}
            />
          </div>
          <button onClick={() => { setPage(1); fetchData(searchInput, filterType, 1); }} style={{
            padding: '8px 16px', borderRadius: '8px', fontSize: '13px',
            background: 'var(--accent)', color: 'white', border: 'none',
            cursor: 'pointer', fontFamily: 'var(--font-body)', fontWeight: 500,
          }}>Search</button>"""
dashboard = dashboard.replace(old_input_end, new_input_end)

with open('app/dashboard/page.tsx', 'w') as f:
    f.write(dashboard)
print("✅ Updated app/dashboard/page.tsx")

print("\n✅ All code fixes applied!")
print("\n⚠️  IMPORTANT: You still need to manually update your Apps Script.")
print("   Copy the code printed above into your Apps Script editor and redeploy as a new version.")
