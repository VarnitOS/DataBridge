import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Input } from "./ui/input";
import { 
  FolderOpen, 
  Clock, 
  Users, 
  CheckCircle, 
  MoreVertical,
  Plus,
  History,
  Download
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface Project {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'draft';
  createdAt: Date;
  lastModified: Date;
  creator: string;
  teamMembers: string[];
  recordsProcessed: number;
  conflictsResolved: number;
  dataQualityScore: number;
}

interface ProjectManagementPanelProps {
  onSelectProject?: (projectId: string) => void;
  onCreateNew?: () => void;
}

export function ProjectManagementPanel({ onSelectProject, onCreateNew }: ProjectManagementPanelProps) {
  const [projects] = useState<Project[]>([
    {
      id: '1',
      name: 'Chase & Wells Fargo Merger Q4 2024',
      status: 'completed',
      createdAt: new Date('2024-10-01'),
      lastModified: new Date('2024-10-03'),
      creator: 'Sarah Johnson',
      teamMembers: ['Sarah Johnson', 'Michael Chen', 'Emily Davis'],
      recordsProcessed: 2450000,
      conflictsResolved: 342,
      dataQualityScore: 96,
    },
    {
      id: '2',
      name: 'Bank of America Integration - Phase 1',
      status: 'active',
      createdAt: new Date('2024-10-04'),
      lastModified: new Date(),
      creator: 'Michael Chen',
      teamMembers: ['Michael Chen', 'Lisa Anderson'],
      recordsProcessed: 1200000,
      conflictsResolved: 128,
      dataQualityScore: 94,
    },
    {
      id: '3',
      name: 'Regional Bank Consolidation - Draft',
      status: 'draft',
      createdAt: new Date('2024-10-03'),
      lastModified: new Date('2024-10-03'),
      creator: 'Emily Davis',
      teamMembers: ['Emily Davis'],
      recordsProcessed: 0,
      conflictsResolved: 0,
      dataQualityScore: 0,
    },
  ]);

  const [searchQuery, setSearchQuery] = useState('');

  const filteredProjects = projects.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="mb-2">Project Workspace</h2>
            <p className="text-muted-foreground">
              Manage your data integration projects
            </p>
          </div>
          <Button onClick={onCreateNew}>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        <Input
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mb-4"
        />

        <ScrollArea className="h-[600px]">
          <div className="space-y-3">
            {filteredProjects.map((project) => (
              <Card
                key={project.id}
                className="p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => onSelectProject?.(project.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 bg-primary/10 rounded-lg mt-1">
                      <FolderOpen className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="mb-1">{project.name}</h3>
                      <div className="flex items-center gap-2 text-muted-foreground mb-2">
                        <Clock className="w-3 h-3" />
                        <span>
                          Last modified: {project.lastModified.toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            project.status === 'completed' ? 'default' :
                            project.status === 'active' ? 'outline' :
                            'secondary'
                          }
                        >
                          {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                        </Badge>
                        {project.dataQualityScore > 0 && (
                          <Badge variant="outline">
                            Quality: {project.dataQualityScore}%
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <History className="w-4 h-4 mr-2" />
                        View History
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Download className="w-4 h-4 mr-2" />
                        Export Report
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Users className="w-4 h-4 mr-2" />
                        Manage Team
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <p className="text-muted-foreground">Records</p>
                    <p>{project.recordsProcessed.toLocaleString()}</p>
                  </div>
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <p className="text-muted-foreground">Conflicts</p>
                    <p>{project.conflictsResolved}</p>
                  </div>
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <p className="text-muted-foreground">Team</p>
                    <p>{project.teamMembers.length} members</p>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Users className="w-4 h-4" />
                    <div className="flex -space-x-2">
                      {project.teamMembers.slice(0, 3).map((member, idx) => (
                        <div
                          key={idx}
                          className="w-6 h-6 rounded-full bg-primary/20 border-2 border-background flex items-center justify-center"
                        >
                          <span className="text-xs">{member.charAt(0)}</span>
                        </div>
                      ))}
                    </div>
                    <span>Created by {project.creator}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}
