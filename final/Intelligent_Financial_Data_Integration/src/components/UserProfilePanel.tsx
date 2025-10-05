import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { 
  User, 
  Moon, 
  Sun, 
  Bell, 
  Database, 
  CreditCard,
  Settings,
  LogOut
} from "lucide-react";
import { Progress } from "./ui/progress";

interface UserProfilePanelProps {
  onThemeToggle?: () => void;
  isDarkMode?: boolean;
}

export function UserProfilePanel({ onThemeToggle, isDarkMode }: UserProfilePanelProps) {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-4 mb-6 pb-6 border-b">
        <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
          <User className="w-8 h-8 text-primary" />
        </div>
        <div className="flex-1">
          <h2>Sarah Johnson</h2>
          <p className="text-muted-foreground">sarah.johnson@ey.com</p>
          <Badge variant="outline" className="mt-2">Enterprise Admin</Badge>
        </div>
      </div>

      <Tabs defaultValue="settings" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="settings">Settings</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="space-y-4 mt-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-3">
                {isDarkMode ? (
                  <Moon className="w-5 h-5 text-primary" />
                ) : (
                  <Sun className="w-5 h-5 text-primary" />
                )}
                <div>
                  <Label>Dark Mode</Label>
                  <p className="text-muted-foreground">Toggle theme preference</p>
                </div>
              </div>
              <Switch checked={isDarkMode} onCheckedChange={onThemeToggle} />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-primary" />
                <div>
                  <Label>Notifications</Label>
                  <p className="text-muted-foreground">Email & push notifications</p>
                </div>
              </div>
              <Switch defaultChecked />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-primary" />
                <div>
                  <Label>Conflict Alerts</Label>
                  <p className="text-muted-foreground">Real-time conflict notifications</p>
                </div>
              </div>
              <Switch defaultChecked />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-3">
                <Settings className="w-5 h-5 text-primary" />
                <div>
                  <Label>Auto-Save Projects</Label>
                  <p className="text-muted-foreground">Automatically save progress</p>
                </div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>

          <div className="pt-4">
            <h4 className="mb-3">Account Security</h4>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <User className="w-4 h-4 mr-2" />
                Update Profile
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Settings className="w-4 h-4 mr-2" />
                Change Password
              </Button>
              <Button variant="outline" className="w-full justify-start text-destructive hover:text-destructive">
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4 mt-6">
          <Card className="p-4 bg-gradient-to-br from-primary/10 to-primary/5">
            <h4 className="mb-4">This Month's Activity</h4>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-muted-foreground">Datasets Merged</span>
                  <span>12 / 50</span>
                </div>
                <Progress value={24} className="h-2" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-muted-foreground">Storage Used</span>
                  <span>3.2 GB / 10 GB</span>
                </div>
                <Progress value={32} className="h-2" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-muted-foreground">AI API Calls</span>
                  <span>1,245 / 5,000</span>
                </div>
                <Progress value={25} className="h-2" />
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <Card className="p-4">
              <Database className="w-8 h-8 text-primary mb-2" />
              <p className="text-muted-foreground">Total Records</p>
              <h2>4.2M</h2>
            </Card>
            <Card className="p-4">
              <Settings className="w-8 h-8 text-primary mb-2" />
              <p className="text-muted-foreground">Projects</p>
              <h2>8</h2>
            </Card>
          </div>

          <Card className="p-4">
            <h4 className="mb-3">Recent Activity</h4>
            <div className="space-y-2">
              {[
                'Completed Chase & Wells Fargo merge',
                'Resolved 342 data conflicts',
                'Generated compliance report',
                'Updated schema mapping rules',
              ].map((activity, idx) => (
                <div key={idx} className="flex items-center gap-2 text-muted-foreground">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                  <span>{activity}</span>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-4 mt-6">
          <Card className="p-4 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
            <div className="flex items-center justify-between mb-2">
              <Badge variant="secondary">Enterprise Plan</Badge>
              <span>$499/month</span>
            </div>
            <h3 className="mb-1">Professional</h3>
            <p className="opacity-90">Unlimited merges, priority support</p>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <CreditCard className="w-5 h-5 text-primary" />
              <h4>Payment Method</h4>
            </div>
            <div className="p-3 bg-muted/30 rounded-lg mb-3">
              <p className="text-muted-foreground">Visa ending in 4242</p>
              <p className="text-muted-foreground">Expires 12/2025</p>
            </div>
            <Button variant="outline" className="w-full">
              Update Payment Method
            </Button>
          </Card>

          <Card className="p-4">
            <h4 className="mb-3">Billing History</h4>
            <div className="space-y-2">
              {[
                { date: 'Oct 1, 2024', amount: '$499.00', status: 'Paid' },
                { date: 'Sep 1, 2024', amount: '$499.00', status: 'Paid' },
                { date: 'Aug 1, 2024', amount: '$499.00', status: 'Paid' },
              ].map((invoice, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/30">
                  <div>
                    <p>{invoice.date}</p>
                    <p className="text-muted-foreground">{invoice.amount}</p>
                  </div>
                  <Badge variant="outline">{invoice.status}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
