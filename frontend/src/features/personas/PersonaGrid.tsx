import { useState } from 'react'
import { PersonaCard } from './PersonaCard'
import { PersonaDetail } from './PersonaDetail'
import { SimulateButton } from './SimulateButton'
import type { Persona } from '../../types'

interface Props {
  personas: Persona[]
}

export function PersonaGrid({ personas }: Props) {
  const [detailId, setDetailId] = useState<string | null>(null)

  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {personas.map((p) => (
          <div key={p.groupId} className="flex flex-col gap-3">
            <PersonaCard
              persona={p}
              onView={() => setDetailId(p.groupId)}
            />
            <SimulateButton groupId={p.groupId} personaName={p.name} />
          </div>
        ))}
      </div>

      {detailId && (
        <PersonaDetail groupId={detailId} onClose={() => setDetailId(null)} />
      )}
    </div>
  )
}
