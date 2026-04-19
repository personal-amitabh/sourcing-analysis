import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { parts } = await req.json();

  // Build a list of unique part+supplier combos not yet enriched
  const unenriched = parts.filter((p: any) => !p['Part Description']);

  if (unenriched.length === 0) {
    return NextResponse.json({ message: 'All parts already enriched', updates: [] });
  }

  // Batch into groups of 20 to avoid huge prompts
  const batch = unenriched.slice(0, 20);

  const prompt = `You are a supply chain expert. I have a list of components used in Resideo products (thermostats, HVAC controls, security systems, water products). 

For each part below, use the supplier name and part number to intelligently identify and fill in as many attributes as you can discover. Resideo suppliers include precision manufacturers of valves, fittings, sensors, PCBs, motors, and mechanical components.

Parts to enrich:
${batch.map((p: any, i: number) => `${i + 1}. Supplier: "${p.Supplier}", Item: "${p.Item}"`).join('\n')}

For each part, return a JSON array where each object has:
- "Item": the exact item number as given
- "Part Description": brief description of what the part likely is
- "Component Type": category (e.g., Valve, Fitting, Sensor, PCB, Motor, Connector, etc.)
- "Material": likely material if determinable (e.g., Brass, Stainless Steel, Plastic, etc.)
- "Manufacturer": the actual manufacturer name (may differ from supplier)
- "Confidence": "High", "Medium", or "Low" based on how certain you are

Return ONLY a valid JSON array, no explanation, no markdown.`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY!,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-4-5',
        max_tokens: 4000,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    const aiData = await response.json();
    const text = aiData.content[0].text;
    const enriched = JSON.parse(text.replace(/```json|```/g, '').trim());

    return NextResponse.json({ updates: enriched, total: unenriched.length, processed: batch.length });
  } catch (err) {
    console.error('Enrichment error:', err);
    return NextResponse.json({ error: 'Enrichment failed' }, { status: 500 });
  }
}
