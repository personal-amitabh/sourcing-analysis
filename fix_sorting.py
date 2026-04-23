dashboard = open('app/dashboard/page.tsx', 'r').read()

# Make sure filtered rows are sorted when sortCol is set
old = """    // Apply search
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
  }, [rows, search, filterType, tileFilter]);"""

new = """    // Apply search
    if (search) {
      const q = search.toLowerCase();
      r = r.filter((row: Row) =>
        String(row.Item || '').toLowerCase().includes(q) ||
        String(row.Supplier || '').toLowerCase().includes(q) ||
        String(row.Plant || '').toLowerCase().includes(q) ||
        String(row['Part Description'] || '').toLowerCase().includes(q)
      );
    }

    // Apply sorting
    if (sortCol) {
      r.sort((a: Row, b: Row) => {
        const av = a[sortCol] ?? '';
        const bv = b[sortCol] ?? '';
        return sortDir === 'asc'
          ? String(av).localeCompare(String(bv))
          : String(bv).localeCompare(String(av));
      });
    }

    return r;
  }, [rows, search, filterType, tileFilter, sortCol, sortDir]);"""

dashboard = dashboard.replace(old, new)
open('app/dashboard/page.tsx', 'w').write(dashboard)
print("✅ Done!")
