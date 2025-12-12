import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  ChangeDetectorRef,
  OnDestroy,
  AfterViewInit,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  ChatbotService,
  ChatMessage,
  Conversation,
  ChatResponse,
} from '../../Service/chatbot.service';
import { Subscription } from 'rxjs';
import { CommonModule, DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-chatbot',
  imports: [DecimalPipe, CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css'],
})
export class ChatbotComponent
  implements OnInit, AfterViewChecked, OnDestroy, AfterViewInit
{
  @ViewChild('messageContainer') private messageContainer!: ElementRef;
  @ViewChild('messageInput') private messageInput!: ElementRef;

  // Form
  messageForm: FormGroup;

  // State
  activeConversation: Conversation | null = null;
  conversations: Conversation[] = [];
  isProcessing = false;
  showSidebar = true;
  showSources = false;
  knowledgeBaseStats: any = null;

  // Suggestions from last response
  currentSuggestions: string[] = [];
  currentSources: any[] = [];

  // Track if we should scroll
  private shouldScroll = false;
  private subscriptions: Subscription[] = [];

  constructor(
    private fb: FormBuilder,
    private chatbotService: ChatbotService,
    private cdRef: ChangeDetectorRef
  ) {
    this.messageForm = this.fb.group({
      message: ['', [Validators.required, Validators.minLength(2)]],
    });
  }

  ngOnInit(): void {
    console.log('ChatbotComponent ngOnInit');

    // Subscribe to active conversation with change detection
    this.subscriptions.push(
      this.chatbotService.activeConversation$.subscribe((conversation) => {
        console.log('Active conversation updated:', {
          id: conversation?.id,
          messageCount: conversation?.messages?.length,
        });

        // Create a new reference to trigger change detection
        this.activeConversation = conversation ? { ...conversation } : null;

        // Force change detection
        this.cdRef.detectChanges();

        // Mark that we should scroll
        this.shouldScroll = true;

        // Scroll after a short delay to ensure DOM is updated
        setTimeout(() => this.scrollToBottom(true), 100);
      })
    );

    // Subscribe to conversations list
    this.subscriptions.push(
      this.chatbotService.conversations$.subscribe((conversations) => {
        this.conversations = conversations;
      })
    );

    // Subscribe to loading state
    this.subscriptions.push(
      this.chatbotService.loading$.subscribe((loading) => {
        console.log('Loading state:', loading);
        this.isProcessing = loading;

        // If loading just finished (response received), scroll
        if (!loading) {
          setTimeout(() => {
            this.shouldScroll = true;
            this.scrollToBottom(true);
          }, 200);
        }
      })
    );

    // Subscribe to knowledge base stats
    this.subscriptions.push(
      this.chatbotService.knowledgeBaseStats$.subscribe((stats) => {
        this.knowledgeBaseStats = stats;
      })
    );

    // Load initial data
    this.loadInitialData();

    // Auto-focus input
    setTimeout(() => this.focusInput(), 100);
  }

  ngAfterViewInit(): void {
    // Initial scroll
    this.scrollToBottom(true);

    // Setup auto-resize
    setTimeout(() => {
      const textarea = this.messageInput?.nativeElement;
      if (textarea) {
        textarea.addEventListener('input', () => this.autoResize());
      }
    }, 100);
  }

  ngAfterViewChecked(): void {
    // Only scroll when we have new content
    if (this.shouldScroll) {
      console.log('Scrolling to bottom, shouldScroll flag');
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  loadInitialData(): void {
    // Check for saved active conversation
    const savedConversationId = localStorage.getItem('activeChatConversation');

    if (savedConversationId) {
      // Try to load the saved conversation
      this.chatbotService.getConversation(savedConversationId).subscribe({
        next: (conversation) => {
          console.log('Loaded saved conversation:', conversation.id);
        },
        error: (error) => {
          console.warn(
            'Saved conversation not found on server, creating new one'
          );
          localStorage.removeItem('activeChatConversation');
          this.createNewChat();
        },
      });
    } else if (this.conversations.length === 0) {
      // Create a new conversation
      this.createNewChat();
    }

    // Load knowledge base stats
    this.chatbotService.loadKnowledgeBaseStats().subscribe();
  }

  /**
   * Send a message - FIXED VERSION
   */
  onSubmit(): void {
    if (this.messageForm.invalid || this.isProcessing) {
      return;
    }

    const message = this.messageForm.get('message')?.value;
    console.log('Sending message:', message);

    if (!this.activeConversation) {
      console.log('No active conversation, creating new one');
      this.createNewChat();
      return;
    }

    // Clear form and reset textarea
    this.messageForm.reset();
    const textarea = this.messageInput?.nativeElement;
    if (textarea) {
      textarea.style.height = 'auto';
    }

    // Send message to backend
    this.chatbotService
      .sendMessage(message, this.activeConversation?.id)
      .subscribe({
        next: (response) => {
          console.log('Message sent successfully:', response);
          this.currentSuggestions = response.suggestions || [];
          this.currentSources = response.sources || [];
          this.focusInput();
        },
        error: (error) => {
          console.error('Failed to send message:', error);

          // Add error message to chat
          if (this.activeConversation) {
            const errorMessage: ChatMessage = {
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
              timestamp: new Date(),
            };

            // Update conversation with error
            const updatedConv = {
              ...this.activeConversation,
              messages: [...this.activeConversation.messages, errorMessage],
            };

            this.chatbotService.setActiveConversation(updatedConv);
          }

          this.focusInput();
        },
      });
  }

  /**
   * Create a new chat - FIXED
   */
  createNewChat(): void {
    console.log('Creating new chat');
    // Clear current state
    this.currentSuggestions = [];
    this.currentSources = [];
    this.showSources = false;

    // Let service create new conversation
    this.chatbotService.createNewConversation();

    this.focusInput();
  }

  /**
   * Select a conversation - FIXED
   */
  selectConversation(conversation: Conversation): void {
    console.log('Selecting conversation:', conversation.id);
    // Clear current suggestions/sources
    this.currentSuggestions = [];
    this.currentSources = [];
    this.showSources = false;

    // Let service handle the selection
    this.chatbotService.setActiveConversation(conversation);

    // Mark for scroll
    this.shouldScroll = true;

    // Close sidebar on mobile
    if (window.innerWidth < 768) {
      this.showSidebar = false;
    }

    this.focusInput();
  }

  // Add this method to properly track messages
  trackByMessage(index: number, message: ChatMessage): string {
    // Use a combination of timestamp and index for uniqueness
    // Simplified version without hashCode to avoid the error
    const timestamp = message.timestamp
      ? new Date(message.timestamp).getTime()
      : Date.now();
    const contentPreview = message.content.substring(0, 20);
    return `${message.role}-${timestamp}-${contentPreview}-${index}`;
  }

  /**
   * Improved scroll to bottom
   */
  private scrollToBottom(force: boolean = false): void {
    setTimeout(() => {
      try {
        if (this.messageContainer?.nativeElement) {
          const element = this.messageContainer.nativeElement;

          // Always scroll when force is true
          if (force) {
            console.log('Forcing scroll to bottom');
            element.scrollTo({
              top: element.scrollHeight,
              behavior: 'smooth',
            });
          } else {
            // Only scroll if we're near the bottom
            const isNearBottom =
              element.scrollHeight - element.scrollTop - element.clientHeight <
              150;

            if (isNearBottom) {
              console.log('Auto-scrolling to bottom (near bottom)');
              element.scrollTo({
                top: element.scrollHeight,
                behavior: 'smooth',
              });
            }
          }
        }
      } catch (err) {
        console.error('Scroll error:', err);
      }
    }, 50);
  }

  /**
   * Focus the message input
   */
  private focusInput(): void {
    setTimeout(() => {
      if (this.messageInput?.nativeElement) {
        this.messageInput.nativeElement.focus();
      }
    }, 100);
  }

  /**
   * Handle key press for sending with Enter
   */
  onKeyPress(event: any): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSubmit();
    }
  }

  /**
   * Auto-resize textarea
   */
  autoResize(): void {
    const textarea = this.messageInput?.nativeElement;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px';
    }
  }

  /**
   * Handle scroll events
   */
  onScroll(): void {
    // You can add scroll-based logic here
  }

  /**
   * Check if message contains code for styling
   */
  containsCode(text: string): boolean {
    return (
      text.includes('```') || text.includes('<code>') || text.includes('`')
    );
  }

  // Other existing methods...
  deleteConversation(conversation: Conversation, event?: MouseEvent): void {
    if (event) {
      event.stopPropagation();
    }

    if (confirm('Are you sure you want to delete this conversation?')) {
      this.chatbotService.deleteConversation(conversation.id).subscribe();
    }
  }

  useSuggestion(suggestion: string): void {
    this.messageForm.patchValue({ message: suggestion });
    this.onSubmit();
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Copied to clipboard');
    });
  }

  refreshKnowledgeBase(): void {
    this.chatbotService.refreshKnowledgeBase().subscribe({
      next: () => {
        console.log('Knowledge base refreshed');
      },
      error: (error) => {
        console.error('Failed to refresh knowledge base:', error);
      },
    });
  }

  formatTime(timestamp: any): string {
    return this.chatbotService.formatMessageTime(timestamp);
  }

  isUserMessage(message: ChatMessage): boolean {
    return this.chatbotService.isUserMessage(message);
  }

  getConversationSummary(conversation: Conversation): string {
    return this.chatbotService.getConversationSummary(conversation);
  }

  toggleSidebar(): void {
    this.showSidebar = !this.showSidebar;
  }

  toggleSources(): void {
    this.showSources = !this.showSources;
  }

  isKnowledgeBaseReady(): boolean {
    return this.knowledgeBaseStats?.status === 'ready';
  }

  // In chatbot.component.ts
  formatMessageContent(content: string): string {
    if (!content) return '';

    // Basic formatting - convert line breaks
    let formatted = content.replace(/\n/g, '<br>');

    // Convert markdown bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert markdown italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert markdown code blocks (simple)
    formatted = formatted.replace(
      /```([\s\S]*?)```/g,
      '<pre class="bg-gray-900 text-white p-4 rounded my-2 overflow-x-auto"><code>$1</code></pre>'
    );

    // Convert inline code
    formatted = formatted.replace(
      /`([^`]+)`/g,
      '<code class="bg-gray-100 px-1 rounded">$1</code>'
    );

    return formatted;
  }
}
