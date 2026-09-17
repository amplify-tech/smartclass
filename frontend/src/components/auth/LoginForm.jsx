import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { login as loginRequest } from '../../api/auth'
import { applyApiErrors } from '../../utils/apiErrors'
import { setTokens } from '../../utils/authTokens'
import { Button, FormField, FormRootError, Input } from '../common_ui'

const loginSchema = z.object({
  email: z.string().trim().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

export default function LoginForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = async (values) => {
    try {
      const { data } = await loginRequest(values)
      setTokens(data)
      window.location.assign('/')
    } catch (error) {
      applyApiErrors(error, setError)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <FormField id="login-email" label="Email" error={errors.email?.message}>
        <Input
          type="email"
          autoComplete="email"
          {...register('email')}
        />
      </FormField>

      <FormField
        id="login-password"
        label="Password"
        error={errors.password?.message}
      >
        <Input
          type="password"
          autoComplete="current-password"
          {...register('password')}
        />
      </FormField>

      <FormRootError message={errors.root?.message} />

      <Button type="submit" block disabled={isSubmitting}>
        {isSubmitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>
  )
}
