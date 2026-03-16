import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/lib/ui/card"

export function SettingsPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure the AI pipeline and search parameters</p>
      </div>
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Settings</CardTitle>
            <CardDescription>Adjust reranker strategy, context format, and search parameters</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Settings configuration coming soon</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
