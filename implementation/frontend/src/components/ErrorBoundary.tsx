import { Component, ReactNode } from 'react';
import { Result, Button, Typography } from 'antd';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo } = this.state;
      const isDev = process.env.NODE_ENV === 'development';

      return (
        <div style={{ padding: 24, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Result
            status="error"
            title="앱에서 오류가 발생했습니다"
            subTitle="예기치 않은 오류가 발생했습니다. 아래 정보를 확인해주세요."
            extra={[
              <Button type="primary" key="home" onClick={this.handleReset}>
                대시보드로 돌아가기
              </Button>,
              <Button key="reload" onClick={this.handleReload}>
                새로고침
              </Button>,
            ]}
          >
            <div style={{ textAlign: 'left', maxWidth: 700, margin: '0 auto' }}>
              <Paragraph>
                <Text strong>에러 유형:</Text> {error?.name || 'Unknown Error'}
              </Paragraph>

              <Paragraph>
                <Text strong>에러 메시지:</Text>
                <pre style={{
                  background: '#fff2f0',
                  padding: 12,
                  borderRadius: 4,
                  overflow: 'auto',
                  maxHeight: 80,
                  fontSize: 12,
                  color: '#cf1322',
                  border: '1px solid #ffccc7',
                }}>
                  {error?.message || '알 수 없는 오류'}
                </pre>
              </Paragraph>

              {isDev && error?.stack && (
                <Paragraph>
                  <Text strong>스택 트레이스:</Text>
                  <pre style={{
                    background: '#f5f5f5',
                    padding: 12,
                    borderRadius: 4,
                    overflow: 'auto',
                    maxHeight: 200,
                    fontSize: 11,
                  }}>
                    {error.stack}
                  </pre>
                </Paragraph>
              )}

              {isDev && errorInfo?.componentStack && (
                <Paragraph>
                  <Text strong>컴포넌트 스택:</Text>
                  <pre style={{
                    background: '#f5f5f5',
                    padding: 12,
                    borderRadius: 4,
                    overflow: 'auto',
                    maxHeight: 150,
                    fontSize: 11,
                  }}>
                    {errorInfo.componentStack}
                  </pre>
                </Paragraph>
              )}

              <Paragraph type="secondary" style={{ marginTop: 16 }}>
                이 오류가 계속 발생하면 관리자에게 문의해주세요.
              </Paragraph>
            </div>
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}
