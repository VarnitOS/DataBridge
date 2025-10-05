import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Avatar } from "./ui/avatar";
import { ScrollArea } from "./ui/scroll-area";
import { MessageSquare, Send, Check, X, Clock, User } from "lucide-react";

interface Comment {
  id: string;
  author: string;
  content: string;
  timestamp: Date;
  fieldName?: string;
  resolved: boolean;
}

interface ApprovalRequest {
  id: string;
  type: 'mapping' | 'resolution' | 'schema';
  description: string;
  requestedBy: string;
  timestamp: Date;
  status: 'pending' | 'approved' | 'rejected';
}

interface CollaborationPanelProps {
  fieldName?: string;
}

export function CollaborationPanel({ fieldName }: CollaborationPanelProps) {
  const [comments, setComments] = useState<Comment[]>([
    {
      id: '1',
      author: 'Sarah Johnson',
      content: 'The mapping for account_number looks good. Should we also normalize the date format?',
      timestamp: new Date('2024-10-04T10:30:00'),
      fieldName: 'account_number',
      resolved: false,
    },
    {
      id: '2',
      author: 'Michael Chen',
      content: 'Agreed. I suggest using ISO 8601 format for all date fields.',
      timestamp: new Date('2024-10-04T10:35:00'),
      fieldName: 'account_number',
      resolved: false,
    },
  ]);

  const [approvals] = useState<ApprovalRequest[]>([
    {
      id: '1',
      type: 'mapping',
      description: 'Schema mapping for customer_id → account_holder_id',
      requestedBy: 'Emily Davis',
      timestamp: new Date('2024-10-04T09:00:00'),
      status: 'pending',
    },
    {
      id: '2',
      type: 'resolution',
      description: 'Auto-resolve 12 duplicate customer records using latest timestamp',
      requestedBy: 'Michael Chen',
      timestamp: new Date('2024-10-04T09:15:00'),
      status: 'pending',
    },
  ]);

  const [newComment, setNewComment] = useState('');

  const handleAddComment = () => {
    if (!newComment.trim()) return;

    const comment: Comment = {
      id: Date.now().toString(),
      author: 'Current User',
      content: newComment,
      timestamp: new Date(),
      fieldName,
      resolved: false,
    };

    setComments(prev => [...prev, comment]);
    setNewComment('');
  };

  const handleResolveComment = (commentId: string) => {
    setComments(prev =>
      prev.map(c => c.id === commentId ? { ...c, resolved: true } : c)
    );
  };

  return (
    <div className="space-y-6">
      {/* Comments Section */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h3>Team Comments</h3>
          <Badge variant="outline">
            {comments.filter(c => !c.resolved).length} Active
          </Badge>
        </div>

        <ScrollArea className="h-64 mb-4">
          <div className="space-y-3 pr-4">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className={`p-3 rounded-lg border ${
                  comment.resolved
                    ? 'bg-muted/30 border-muted'
                    : 'bg-card border-border'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span>{comment.author}</span>
                      {comment.fieldName && (
                        <Badge variant="outline" className="text-xs">
                          {comment.fieldName}
                        </Badge>
                      )}
                      {comment.resolved && (
                        <Badge variant="outline" className="text-xs gap-1">
                          <Check className="w-3 h-3" />
                          Resolved
                        </Badge>
                      )}
                    </div>
                    <p className="text-muted-foreground mb-2">{comment.content}</p>
                    <div className="flex items-center gap-3">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {comment.timestamp.toLocaleTimeString()}
                      </span>
                      {!comment.resolved && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleResolveComment(comment.id)}
                        >
                          <Check className="w-3 h-3 mr-1" />
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="flex gap-2">
          <Textarea
            placeholder="Add a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="min-h-[60px]"
          />
          <Button onClick={handleAddComment} className="self-end">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </Card>

      {/* Approval Workflow Section */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Check className="w-5 h-5 text-primary" />
          <h3>Pending Approvals</h3>
          <Badge variant="outline">
            {approvals.filter(a => a.status === 'pending').length}
          </Badge>
        </div>

        <div className="space-y-3">
          {approvals.map((approval) => (
            <div
              key={approval.id}
              className="p-4 rounded-lg border bg-card"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <Badge variant="outline" className="mb-2">
                    {approval.type.charAt(0).toUpperCase() + approval.type.slice(1)}
                  </Badge>
                  <p>{approval.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-muted-foreground">
                  Requested by {approval.requestedBy}
                </span>
                <span className="text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {approval.timestamp.toLocaleDateString()}
                </span>
              </div>
              {approval.status === 'pending' && (
                <div className="flex gap-2">
                  <Button size="sm" variant="default" className="flex-1">
                    <Check className="w-4 h-4 mr-1" />
                    Approve
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <X className="w-4 h-4 mr-1" />
                    Reject
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Team Members */}
      <Card className="p-6">
        <h3 className="mb-4">Team Members</h3>
        <div className="space-y-3">
          {[
            { name: 'Sarah Johnson', role: 'Admin', status: 'online' },
            { name: 'Michael Chen', role: 'Editor', status: 'online' },
            { name: 'Emily Davis', role: 'Editor', status: 'offline' },
            { name: 'Lisa Anderson', role: 'Viewer', status: 'away' },
          ].map((member, idx) => (
            <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/30">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                  <div
                    className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-background ${
                      member.status === 'online'
                        ? 'bg-green-500'
                        : member.status === 'away'
                        ? 'bg-yellow-500'
                        : 'bg-muted-foreground'
                    }`}
                  />
                </div>
                <div>
                  <p>{member.name}</p>
                  <p className="text-muted-foreground">{member.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
