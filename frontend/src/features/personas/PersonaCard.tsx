import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import type { Persona } from '../../types'

interface Props {
  persona: Persona
  onView: () => void
}

export function PersonaCard({ persona, onView }: Props) {
  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white">{persona.name}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          {persona.origin} · {persona.sophistication}
        </p>
      </div>
      <div className="flex flex-wrap gap-1">
        {persona.motivations.map((m) => (
          <Badge key={m} color="blue">{m}</Badge>
        ))}
      </div>
      <div className="flex flex-wrap gap-1">
        {persona.signatureTTPs.slice(0, 3).map((t) => (
          <Badge key={t.techniqueId} color="gray">{t.techniqueId}</Badge>
        ))}
        {persona.signatureTTPs.length > 3 && (
          <Badge color="gray">+{persona.signatureTTPs.length - 3}</Badge>
        )}
      </div>
      <div className="flex gap-2 mt-auto pt-2 border-t border-gray-100 dark:border-gray-800">
        <Button variant="secondary" size="sm" onClick={onView}>View</Button>
      </div>
    </Card>
  )
}
