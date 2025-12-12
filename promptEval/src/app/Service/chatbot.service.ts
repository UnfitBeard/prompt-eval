// services/chatbot.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap, map, shareReplay } from 'rxjs/operators';
import { environment } from '../environments/environment';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  include_context?: boolean;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  context_used: boolean;
  suggestions: string[];
  sources: Array<{
    source: string;
    title: string;
    relevance: number;
  }>;
  processing_time_ms: number;
}

export interface Conversation {
  id: string;
  messages: ChatMessage[];
  created_at: Date;
  updated_at: Date;
  title?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ChatbotService {
  private apiUrl = environment.apiUrl;

  // State management
  private activeConversationSubject = new BehaviorSubject<Conversation | null>(
    null
  );
  private conversationsSubject = new BehaviorSubject<Conversation[]>([]);
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private knowledgeBaseStatsSubject = new BehaviorSubject<any>(null);

  // Public observables
  activeConversation$ = this.activeConversationSubject.asObservable();
  conversations$ = this.conversationsSubject.asObservable();
  loading$ = this.loadingSubject.asObservable();
  knowledgeBaseStats$ = this.knowledgeBaseStatsSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadConversations();
    this.loadKnowledgeBaseStats();
  }

  /**
   * Load all conversations
   */
  loadConversations(limit: number = 20): Observable<Conversation[]> {
    return this.http
      .post<Conversation[]>(
        `${this.apiUrl}/api/v1/chat/conversations?limit=${limit}`,
        {}
      )
      .pipe(
        tap((conversations) => {
          this.conversationsSubject.next(conversations);

          // If there's no active conversation, set the most recent one
          if (
            !this.activeConversationSubject.value &&
            conversations.length > 0
          ) {
            this.setActiveConversation(conversations[0]);
          }
        }),
        catchError((error) => {
          console.error('Failed to load conversations:', error);
          return throwError(() => new Error('Failed to load conversations'));
        })
      );
  }

  /**
   * Get a specific conversation
   */
  getConversation(id: string): Observable<Conversation> {
    return this.http
      .get<Conversation>(`${this.apiUrl}/api/v1/chat/conversation/${id}`)
      .pipe(
        tap((conversation) => this.setActiveConversation(conversation)),
        catchError((error) => {
          console.error('Failed to get conversation:', error);
          return throwError(() => new Error('Failed to load conversation'));
        })
      );
  }

  /**
   * Set active conversation
   */
  setActiveConversation(conversation: Conversation | null): void {
    this.activeConversationSubject.next(conversation);

    // Save to localStorage for persistence
    if (conversation) {
      localStorage.setItem('activeChatConversation', conversation.id);
    } else {
      localStorage.removeItem('activeChatConversation');
    }
  }

  /**
   * Delete a conversation
   */
  deleteConversation(id: string): Observable<any> {
    return this.http
      .delete(`${this.apiUrl}/api/v1/chat/conversation/${id}`)
      .pipe(
        tap(() => {
          // Remove from local list
          const current = this.conversationsSubject.value;
          const updated = current.filter((conv) => conv.id !== id);
          this.conversationsSubject.next(updated);

          // If deleting active conversation, clear it
          if (this.activeConversationSubject.value?.id === id) {
            this.setActiveConversation(null);
          }
        }),
        catchError((error) => {
          console.error('Failed to delete conversation:', error);
          return throwError(() => new Error('Failed to delete conversation'));
        })
      );
  }

  /**
   * Refresh knowledge base
   */
  refreshKnowledgeBase(): Observable<any> {
    return this.http
      .post(`${this.apiUrl}/api/v1/chat/knowledge-base/refresh`, {})
      .pipe(
        tap(() => {
          // Reload stats after refresh
          setTimeout(() => this.loadKnowledgeBaseStats(), 2000);
        }),
        catchError((error) => {
          console.error('Failed to refresh knowledge base:', error);
          return throwError(
            () => new Error('Failed to refresh knowledge base')
          );
        })
      );
  }

  /**
   * Load knowledge base statistics
   */
  loadKnowledgeBaseStats(): Observable<any> {
    return this.http
      .get(`${this.apiUrl}/api/v1/chat/knowledge-base/stats`)
      .pipe(
        tap((stats) => this.knowledgeBaseStatsSubject.next(stats)),
        catchError((error) => {
          console.error('Failed to load knowledge base stats:', error);
          return throwError(
            () => new Error('Failed to load knowledge base stats')
          );
        })
      );
  }

  /**
   * Format timestamp for display
   */
  formatMessageTime(timestamp: Date | string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Get conversation summary (for sidebar)
   */
  getConversationSummary(conversation: Conversation): string {
    if (conversation.title) {
      return conversation.title;
    }

    if (conversation.messages.length > 0) {
      const firstMessage = conversation.messages[0];
      return (
        firstMessage.content.substring(0, 50) +
        (firstMessage.content.length > 50 ? '...' : '')
      );
    }

    return 'Empty Chat';
  }

  /**
   * Check if message is from user
   */
  isUserMessage(message: ChatMessage): boolean {
    return message.role === 'user';
  }

  /**
   * Add conversation to list
   */
  private addConversationToList(conversation: Conversation): void {
    const current = this.conversationsSubject.value;
    this.conversationsSubject.next([conversation, ...current]);
  }

  /**
   * Update conversation in list
   */
  private updateConversationInList(conversation: Conversation): void {
    const current = this.conversationsSubject.value;
    const updated = current.map((conv) =>
      conv.id === conversation.id ? conversation : conv
    );

    // Move to top of list
    const index = updated.findIndex((conv) => conv.id === conversation.id);
    if (index > 0) {
      const [moved] = updated.splice(index, 1);
      updated.unshift(moved);
    }

    this.conversationsSubject.next(updated);
  }

  /**
   * Generate a unique ID
   */
  private generateId(): string {
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // services/chatbot.service.ts - Update this method

  /**
   * Update conversation with new response
   */
  private updateConversationWithResponse(response: ChatResponse): void {
    const currentConversation = this.activeConversationSubject.value;

    console.log('Updating conversation with response:', {
      currentId: currentConversation?.id,
      responseId: response.conversation_id,
      hasMessages: currentConversation?.messages?.length,
    });

    if (
      !currentConversation ||
      currentConversation.id !== response.conversation_id
    ) {
      // Load the conversation from the response
      console.log('Loading conversation from response');
      this.getConversation(response.conversation_id).subscribe();
      return;
    }

    // Create assistant message
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: response.response, // Note: using response.response not response.content
      timestamp: new Date(),
    };

    // Create a NEW conversation object with the updated messages
    const updatedConversation: Conversation = {
      ...currentConversation,
      updated_at: new Date(),
      messages: [...currentConversation.messages, assistantMessage], // Add assistant message
    };

    console.log(
      'Updated conversation messages:',
      updatedConversation.messages.length
    );

    // Update the active conversation
    this.setActiveConversation(updatedConversation);

    // Update in conversations list
    this.updateConversationInList(updatedConversation);
  }

  /**
   * Send a message to the chatbot - Also update this method
   */
  sendMessage(
    message: string,
    conversationId?: string
  ): Observable<ChatResponse> {
    this.loadingSubject.next(true);

    // First, add user message to local state immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date(),
    };

    let currentConv = this.activeConversationSubject.value;

    // If no conversation exists, create a new one
    if (!currentConv) {
      this.createNewConversation();
      currentConv = this.activeConversationSubject.value;
    }

    if (currentConv) {
      // Add user message to local conversation immediately
      const tempConversation: Conversation = {
        ...currentConv,
        updated_at: new Date(),
        messages: [...currentConv.messages, userMessage],
      };

      this.setActiveConversation(tempConversation);
      this.updateConversationInList(tempConversation);
    }

    const request: ChatRequest = {
      message: message.trim(),
      conversation_id: currentConv?.id || conversationId,
      include_context: true,
    };

    return this.http
      .post<ChatResponse>(`${this.apiUrl}/api/v1/chat/ask`, request)
      .pipe(
        tap((response) => {
          console.log('Received response:', response);
          // Update or create conversation with assistant response
          this.updateConversationWithResponse(response);
          this.loadingSubject.next(false);
        }),
        catchError((error) => {
          this.loadingSubject.next(false);
          console.error('Chat error:', error);
          return throwError(
            () => new Error('Failed to send message. Please try again.')
          );
        })
      );
  }

  /**
   * Create a new conversation - Update this method too
   */
  createNewConversation(): void {
    const newConversation: Conversation = {
      id: this.generateId(),
      messages: [],
      created_at: new Date(),
      updated_at: new Date(),
      title: 'New Chat',
    };

    console.log('Creating new conversation:', newConversation.id);
    this.setActiveConversation(newConversation);
    this.addConversationToList(newConversation);
  }
}
