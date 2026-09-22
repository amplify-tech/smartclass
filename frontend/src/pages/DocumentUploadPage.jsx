import { useState } from 'react'

import DocumentUploadForm from '../components/documents/DocumentUploadForm'
import { Box, Card, CardBody, PageHeader } from '../components/common_ui'

const PHASE_COPY = {
  form: {
    title: 'Upload Document',
    description: 'Add a document to your teaching materials.',
  },
  uploading: {
    title: 'Uploading document',
    description: undefined,
  },
  success: {
    title: '✓ Document uploaded',
    description: undefined,
  },
  error: {
    title: 'Upload failed',
    description: undefined,
  },
}

export default function DocumentUploadPage() {
  const [phase, setPhase] = useState('form')
  const copy = PHASE_COPY[phase] || PHASE_COPY.form

  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Documents', to: '/documents' },
          { label: phase === 'form' ? 'Upload' : copy.title },
        ]}
        title={copy.title}
        description={copy.description}
      />
      <Card>
        <CardBody className="sc-card-body">
          <DocumentUploadForm onPhaseChange={setPhase} />
        </CardBody>
      </Card>
    </Box>
  )
}
